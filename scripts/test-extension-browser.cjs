#!/usr/bin/env node
/* Real Chromium, fresh temporary profile, original unpacked extension.
 * Only a loopback HTTP/WebSocket fixture is contacted. No Meta account.
 * Requires playwright and ws (resolve via NODE_PATH if not installed locally).
 * Usage: node scripts/test-extension-browser.cjs /path/to/chrome
 */
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { WebSocketServer } = require('ws');
const extension = path.resolve(process.argv[2] || '');
if (!process.argv[2]) throw Error('Pass the extracted chrome directory');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'muse-synthetic-browser-'));
const frames = [];
const peers = [];
let browser;
let port;
const server = http.createServer((req, res) => {
  if (req.url === '/identity') {
    res.setHeader('Content-Type', 'application/json'); res.end('{}'); return;
  }
  res.setHeader('Content-Type', 'text/html');
  res.end('<!doctype html><title>SYNTHETIC_BROWSER_TITLE</title><input id="synthetic"><p>SYNTHETIC_PAGE_CONTENT</p>');
});
const wss = new WebSocketServer({ server, path: '/ws' });
wss.on('connection', ws => {
  peers.push(ws);
  ws.on('message', raw => {
    const msg = JSON.parse(raw.toString()); frames.push(msg);
    if (msg.type === 'req' && (msg.method === 'node.register' || msg.method === 'node.heartbeat')) {
      ws.send(JSON.stringify({ type: 'res', id: msg.id, status: 'ok', payload: {} }));
    }
  });
});
const until = async (fn, message) => {
  const end = Date.now() + 10000;
  while (Date.now() < end) { const value = await fn(); if (value) return value; await new Promise(r => setTimeout(r, 50)); }
  throw Error('Timeout: ' + message);
};
async function launch() {
  browser = await chromium.launchPersistentContext(profile, {
    channel: 'chromium', headless: true,
    ...(process.env.MUSE_TEST_CHROMIUM ? { executablePath: process.env.MUSE_TEST_CHROMIUM } : {}),
    args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`,
      '--disable-background-networking', '--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1'],
  });
  return browser.serviceWorkers()[0] || await browser.waitForEvent('serviceworker');
}
async function status(worker) { return worker.evaluate(() => connection.status()); }
async function invoke(id, command, params) {
  peers.at(-1).send(JSON.stringify({ type: 'req', method: 'node.invoke.request', params: { request_id: id, command, params } }));
  return until(() => frames.find(m => m.method === 'node.invoke.result' && m.params.request_id === id), id);
}
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve)); port = server.address().port;
  let worker = await launch();
  if (process.env.MUSE_TEST_DEBUG) {
    browser.on('console', m => console.error('[browser]', m.text()));
    browser.on('weberror', e => console.error('[browser-error]', e.error().message));
  }
  await worker.evaluate(async () => { await _bundledReady; await connection.connect(); });
  await worker.evaluate(async ({ port }) => {
    await connection.pair('SYNTHETIC_LOOPBACK_TOKEN', `ws://127.0.0.1:${port}/ws`, 'manual');
  }, { port });
  await until(async () => (await status(worker)).registered, 'register first connection');
  await worker.evaluate(() => connection.setPaused(true));
  const before = frames.length;
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${port}/synthetic?marker=SYNTHETIC_URL`);
  const event = await until(() => frames.slice(before).find(m => m.event === 'browser.page_loaded' && m.payload?.title === 'SYNTHETIC_BROWSER_TITLE'), 'paused browser event');
  assert.equal((await status(worker)).paused, true);
  const blockedCommand = await invoke('paused-command', 'tabs.list', {});
  assert.equal(blockedCommand.params.result.error.code, 'paused');
  const cachedPause = await worker.evaluate(async () => (await chrome.storage.local.get('_cachedStatus'))._cachedStatus.paused);
  assert.equal(cachedPause, true);
  await browser.close(); browser = null;
  worker = await launch();
  // Opening the extension popup wakes its normal status/reconnect path.
  const extensionId = new URL(worker.url()).host;
  const popup = await browser.newPage();
  await popup.goto(`chrome-extension://${extensionId}/popup.html`);
  await until(async () => (await status(worker)).registered, 'reconnect after browser restart');
  const afterRestart = await status(worker);
  assert.equal(afterRestart.paused, false);
  const afterRestartResult = await invoke('post-restart-command', 'tabs.list', {});
  assert.equal(afterRestartResult.params.result.ok, true);
  const syntheticPage = await browser.newPage();
  await syntheticPage.goto(`http://127.0.0.1:${port}/typing`);
  const tabId = await worker.evaluate(async ({ port }) => {
    const tabs = await chrome.tabs.query({}); return tabs.find(t => t.url === `http://127.0.0.1:${port}/typing`).id;
  }, { port });
  const typed = await invoke('typed-synthetic', 'page.type', { tab_id: tabId, selector: '#synthetic', value: 'SYNTHETIC_TYPED_BROWSER_VALUE' });
  assert.equal(typed.params.result.ok, true);
  assert.equal(await syntheticPage.locator('#synthetic').inputValue(), 'SYNTHETIC_TYPED_BROWSER_VALUE');
  await worker.evaluate(() => connection.unpair());
  const retained = await worker.evaluate(async () => {
    const d = await chrome.storage.local.get(['authToken', '_cachedStatus']);
    return { tokenPresent: Boolean(d.authToken), lastCommand: d._cachedStatus?.lastCommand };
  });
  assert.equal(retained.tokenPresent, false);
  assert.equal(retained.lastCommand.params.value, 'SYNTHETIC_TYPED_BROWSER_VALUE');
  const normalize = obj => JSON.parse(JSON.stringify(obj).replaceAll(String(port), 'LOOPBACK_PORT'));
  console.log(JSON.stringify({
    scope: 'Real isolated Chromium with the original extension, synthetic pages and a loopback gateway using the manual pairing path. No Meta login, cloud traffic, native Muse execution or production gateway acceptance tested.',
    chromium_version: browser.browser().version(),
    extension_version: JSON.parse(fs.readFileSync(path.join(extension, 'manifest.json'))).version,
    source_sha256: Object.fromEntries(['background.js', 'lib/connection.js', 'lib/events.js', 'lib/commands.js'].map(f => [f, crypto.createHash('sha256').update(fs.readFileSync(path.join(extension, f))).digest('hex')])),
    results: {
      paused_event_received_at_loopback_gateway: normalize(event),
      fresh_command_while_paused: blockedCommand.params.result,
      pause_cached_before_browser_restart: cachedPause,
      pause_after_browser_restart: afterRestart.paused,
      tabs_list_succeeded_after_browser_restart: afterRestartResult.params.result.ok,
      synthetic_page_type_executed: true,
      after_unpair: normalize(retained),
    },
  }, null, 2));
})().catch(e => { console.error(e); process.exitCode = 1; }).finally(async () => {
  if (browser) await browser.close();
  for (const ws of peers) ws.terminate();
  await new Promise(resolve => wss.close(resolve));
  await new Promise(resolve => server.close(resolve));
  fs.rmSync(profile, { recursive: true, force: true });
});
