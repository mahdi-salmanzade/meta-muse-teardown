#!/usr/bin/env node
/* Offline behavioral tests of the original shipped JavaScript.
 * Usage: node scripts/test-extension-boundaries.cjs /path/to/Muse.app/Contents/Resources/chrome
 * No browser profile, account, actual socket, or app process is used.
 * Chrome storage/events, WebSocket and command execution are deterministic fakes.
 * This tests the connection/event implementation, not Chrome or Meta's servers.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(process.argv[2] || '');
if (!process.argv[2]) throw Error('Pass the extracted chrome directory');
const files = ['lib/protocol.js', 'lib/pairing-security.js', 'lib/blocked-sites.js', 'lib/connection.js', 'lib/events.js'];
const sources = Object.fromEntries(files.map(f => [f, fs.readFileSync(path.join(root, f), 'utf8')]));
const hashes = Object.fromEntries(files.map(f => [f, crypto.createHash('sha256').update(sources[f]).digest('hex')]));
const clone = x => x === undefined ? undefined : JSON.parse(JSON.stringify(x));
const tests = [];

function fixture(shared = null) {
  const data = shared || { local: {}, session: {}, sync: {} };
  const events = {};
  const sockets = [];
  const calls = [];
  const logs = [];
  let impl = async () => ({ ok: true, payload_json: JSON.stringify({ marker: 'SYNTHETIC_RESULT_A' }) });
  function storage(name) {
    return {
      async get(keys) {
        if (keys === null) return clone(data[name]);
        const selected = typeof keys === 'string' ? [keys] : keys;
        return Object.fromEntries(selected.filter(k => k in data[name]).map(k => [k, clone(data[name][k])]));
      },
      async set(values) { Object.assign(data[name], clone(values)); },
      async remove(keys) { for (const k of typeof keys === 'string' ? [keys] : keys) delete data[name][k]; },
    };
  }
  function event(name) { return { addListener(fn) { events[name] = fn; } }; }
  class FakeSocket {
    static OPEN = 1;
    static CONNECTING = 0;
    constructor(url) { this.url = url; this.readyState = 0; this.sent = []; sockets.push(this); }
    send(raw) { this.sent.push(JSON.parse(raw)); }
    close() { this.readyState = 3; }
  }
  let nextId = 0;
  const context = vm.createContext({
    URL, Date: class extends Date { static now() { return 1801000000000; } },
    crypto: { randomUUID: () => `synthetic-id-${++nextId}` },
    navigator: { userAgent: 'SYNTHETIC macOS' },
    console: Object.fromEntries(['log','warn','error'].map(k => [k, (...x) => logs.push(x.join(' '))])),
    WebSocket: FakeSocket,
    setTimeout: () => 1, clearTimeout: () => {}, setInterval: () => 1, clearInterval: () => {},
    fetch: () => { throw Error('Network access forbidden in this harness'); },
    chrome: {
      storage: { local: storage('local'), session: storage('session'), sync: storage('sync') },
      alarms: { clear: async () => true, create: () => {} },
      runtime: { getManifest: () => ({ version: '1.0.8' }), lastError: null },
      tabs: {
        onActivated: event('tabActivated'), onUpdated: event('tabUpdated'),
        onCreated: event('tabCreated'), onRemoved: event('tabRemoved'),
        get: (id, cb) => cb({ id, windowId: 1, url: 'https://example.com/private?marker=SYNTHETIC', title: 'SYNTHETIC_TITLE' }),
      },
      downloads: {
        onChanged: event('downloadChanged'),
        search: (q, cb) => cb([{ id: q.id, filename: '/synthetic/SYNTHETIC_FILE.pdf', url: 'https://example.com/download', finalUrl: 'https://example.com/download' }]),
      },
      notifications: { onClicked: event('notificationClicked') },
    },
    executeCommand: async (command, params) => { calls.push({ command, params: clone(params) }); return impl(command, params); },
  });
  for (const f of files) vm.runInContext(sources[f], context, { filename: f, timeout: 1000 });
  vm.runInContext('globalThis.testConnection = new HatchConnection(); initEvents(event => testConnection.send(event));', context);
  const c = context.testConnection;
  return {
    c, data, events, sockets, calls, context,
    setImpl(fn) { impl = fn; },
    async pair(label = 'a', expiresAt = 1900000000000) {
      await c.pair(`SYNTHETIC_TOKEN_${label}`, `wss://synthetic-${label}.metaaivm.com/ws`, 'hatch-web', null, null,
        { gatewayIdentity: `synthetic-${label}.metaaivm.com`, expiresAt });
      const s = sockets.at(-1); s.readyState = FakeSocket.OPEN;
      // Registration is deliberately assumed: the server is outside test scope.
      c.registered = true;
      return s;
    },
  };
}
async function test(id, name, fn) {
  const observation = await fn();
  tests.push({ id, name, observation });
}
const invoke = (id, command = 'page.type', params = { value: 'SYNTHETIC_TYPED_VALUE', selector: '#synthetic' }) => ({ request_id: id, command, params });

(async () => {
  await test('B01', 'Pause blocks a fresh command', async () => {
    const f = fixture(); const s = await f.pair(); f.c.setPaused(true);
    await f.c._handleInvoke(invoke('fresh'));
    assert.equal(f.calls.length, 0); assert.equal(s.sent.at(-1).params.result.error.code, 'paused');
    return { command_executed: false, result: 'paused' };
  });
  await test('B02', 'Pause does not suppress browser event metadata', async () => {
    const f = fixture(); const s = await f.pair(); f.c.setPaused(true);
    f.events.tabActivated({ tabId: 7, windowId: 1 });
    f.events.tabUpdated(7, { status: 'complete', url: 'https://example.com/private?marker=SYNTHETIC' }, { url: 'https://example.com/private?marker=SYNTHETIC', title: 'SYNTHETIC_TITLE' });
    f.events.downloadChanged({ id: 9, state: { current: 'complete' } });
    assert.equal(s.sent.length, 4);
    assert.ok(JSON.stringify(s.sent).includes('SYNTHETIC_FILE.pdf'));
    return { paused: f.c.paused, frames_at_mock_socket: s.sent };
  });
  await test('B03', 'Blocked-site metadata is suppressed', async () => {
    const f = fixture(); const s = await f.pair();
    const blocked = ['https://hatch.meta.ai/private', 'https://a.internalfb.com/private', 'https://web.whatsapp.com/', 'file:///synthetic/private', 'http://localhost:9222/json'];
    for (const url of blocked) f.events.tabUpdated(1, { status: 'complete', url }, { url, title: 'SYNTHETIC_BLOCKED' });
    assert.equal(s.sent.length, 0);
    return { inputs: blocked, frames_at_mock_socket: 0 };
  });
  await test('B04', 'Pause is not restored after worker reconstruction', async () => {
    const f = fixture(); await f.pair(); f.c.setPaused(true);
    assert.equal(f.data.local._cachedStatus.paused, true);
    const g = fixture(f.data); await g.c.connect();
    const s = g.sockets.at(-1); s.readyState = 1; g.c.registered = true;
    await g.c._handleInvoke(invoke('after-worker-restart'));
    assert.equal(g.c.paused, false); assert.equal(g.calls.length, 1);
    return { persisted_cached_pause_before_restart: true, new_connection_paused: false, synthetic_command_executed: true };
  });
  await test('B05', 'Unpair clears credentials but retains last command parameters', async () => {
    const f = fixture(); await f.pair(); await f.c._handleInvoke(invoke('typed')); await f.c.unpair();
    assert.equal(f.data.local.authToken, undefined);
    assert.equal(f.data.local._cachedStatus.lastCommand.params.value, 'SYNTHETIC_TYPED_VALUE');
    return { credential_removed: true, cached_last_command: f.data.local._cachedStatus.lastCommand };
  });
  await test('B06', 'Unpaired browser events do not leave the connection', async () => {
    const f = fixture(); const s = await f.pair(); await f.c.unpair(); f.events.tabActivated({ tabId: 7, windowId: 1 });
    assert.equal(s.sent.length, 0); assert.equal(f.c.ws, null);
    return { frames_after_unpair: 0 };
  });
  await test('B07', 'Expired credentials are loaded and passed to socket construction', async () => {
    const f = fixture(); await f.pair('a', 1);
    const g = fixture(f.data); await g.c.connect();
    assert.equal(g.sockets.length, 1); assert.equal(g.c.expiresAt, 1);
    return { expired_timestamp: 1, mock_socket_constructed: true, server_acceptance: 'not tested' };
  });
  await test('B08', 'Web pairing rejects insecure and foreign hosts', async () => {
    const f = fixture(); const p = f.context.hatchPairingSecurity;
    const urls = ['ws://synthetic-a.metaaivm.com/ws', 'wss://example.com/ws', 'wss://x.metaaivm.com.example.com/ws', 'wss://metaaivm.com/ws'];
    for (const url of urls) assert.equal(p.normalizeWsUrlForCredentialSource(url, 'hatch-web'), null);
    return { rejected: urls };
  });
  await test('B09', 'Retired native-lane credentials are discarded', async () => {
    const f = fixture(); Object.assign(f.data.local, { credentialSource: 'endo', authToken: 'SYNTHETIC', wsUrl: 'wss://example.com/ws' });
    await f.c.connect(); assert.equal(f.sockets.length, 0); assert.equal(f.data.local.authToken, undefined);
    return { mock_socket_constructed: false, credential_removed: true };
  });
  await test('B10', 'A duplicate returns cached data even while paused', async () => {
    const f = fixture(); const s = await f.pair(); await f.c._handleInvoke(invoke('same-id', 'page.get_text', {}));
    f.c.setPaused(true); await f.c._handleInvoke(invoke('same-id', 'page.get_text', {}));
    assert.equal(f.calls.length, 1); assert.equal(s.sent.length, 2);
    assert.equal(s.sent[1].params.result.payload_json, s.sent[0].params.result.payload_json);
    return { executions: 1, cached_result_replayed_while_paused: true };
  });
  await test('B11', 'Unpair/re-pair retains the request-result cache', async () => {
    const f = fixture(); await f.pair('a'); await f.c._handleInvoke(invoke('shared-id', 'page.get_text', {}));
    await f.c.unpair(); const b = await f.pair('b'); await f.c._handleInvoke(invoke('shared-id', 'page.get_text', {}));
    assert.equal(f.calls.length, 1); assert.ok(b.sent.at(-1).params.result.payload_json.includes('SYNTHETIC_RESULT_A'));
    return { executions: 1, previous_connection_result_replayed_to_new_mock_socket: true, production_request_id_reuse: 'not established' };
  });
  await test('B12', 'An in-flight result can complete on a replacement connection', async () => {
    const f = fixture(); await f.pair('a'); let finish;
    f.setImpl(() => new Promise(resolve => { finish = resolve; }));
    const pending = f.c._handleInvoke(invoke('in-flight-a', 'page.get_text', {}));
    assert.equal(typeof finish, 'function');
    await f.c.unpair(); const b = await f.pair('b');
    finish({ ok: true, payload_json: JSON.stringify({ marker: 'SYNTHETIC_RESULT_FROM_A' }) }); await pending;
    assert.equal(b.sent.length, 1); assert.ok(b.sent[0].params.result.payload_json.includes('SYNTHETIC_RESULT_FROM_A'));
    return { old_invocation_result_at_new_mock_socket: b.sent[0], production_cross_account_exposure: 'not tested' };
  });
  await test('B13', 'Pause does not cancel an already-running command', async () => {
    const f = fixture(); const s = await f.pair(); let finish;
    f.setImpl(() => new Promise(resolve => { finish = resolve; }));
    const pending = f.c._handleInvoke(invoke('in-flight-pause', 'page.get_text', {}));
    f.c.setPaused(true); finish({ ok: true, payload_json: '"SYNTHETIC_LATE_RESULT"' }); await pending;
    assert.equal(s.sent.length, 1); assert.equal(s.sent[0].params.result.ok, true);
    return { paused: true, in_flight_result_sent: true };
  });
  await test('B14', 'Invalid pairing event sources and lookalike senders are rejected', async () => {
    const f = fixture(); const p = f.context.hatchPairingSecurity;
    for (const event of [{}, { source: {}, isTrusted: true, origin: 'https://hatch.meta.ai' }]) {
      assert.equal(p.parseHatchWebPairEvent(event, 'https://hatch.meta.ai').ok, false);
    }
    assert.equal(p.isAllowedHatchWebSender({ url: 'https://hatch.meta.ai.example.com/' }), false);
    return { rejected_event_cases: 2, lookalike_sender_rejected: true };
  });
  console.log(JSON.stringify({
    scope: 'Original shipped connection, pairing, protocol and event JS in a Node VM with mocked Chrome APIs, sockets and command results. No Muse app launch, real browser traffic, server acceptance or account isolation test.',
    extension_version: JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'))).version,
    input_sha256: hashes, tests_completed: tests.length, tests,
  }, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
