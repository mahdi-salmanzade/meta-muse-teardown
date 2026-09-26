/* Selective DEX disassembly without relying on JADX's reconstructed branches.
 * Use the smali/dexlib classes bundled in JADX 1.5.5:
 * java -cp /path/to/jadx-all.jar scripts/DisassembleSelected.java sample.apk output-dir class.name ...
 * Exact classes and their nested classes are selected. Does not execute APK code.
 */
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import com.android.tools.smali.baksmali.Baksmali;
import com.android.tools.smali.baksmali.BaksmaliOptions;
import com.android.tools.smali.dexlib2.DexFileFactory;
import com.android.tools.smali.dexlib2.Opcodes;

class DisassembleSelected {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) throw new IllegalArgumentException("APK output-dir class.name ...");
        var container = DexFileFactory.loadDexContainer(new File(args[0]), Opcodes.getDefault());
        var options = new BaksmaliOptions();
        options.codeOffsets = true;
        int total = 0;
        for (var name : container.getDexEntryNames()) {
            var dex = container.getEntry(name).getDexFile();
            List<String> selected = new ArrayList<>();
            for (var cls : dex.getClasses()) {
                String type = cls.getType();
                for (int i = 2; i < args.length; i++) {
                    String target = "L" + args[i].replace('.', '/');
                    if (type.equals(target + ";") || type.startsWith(target + "$")) {
                        selected.add(type); break;
                    }
                }
            }
            if (!selected.isEmpty()) {
                if (!Baksmali.disassembleDexFile(dex, new File(args[1], name), 2, options, selected))
                    throw new IllegalStateException("Disassembly failed: " + name);
                total += selected.size();
            }
        }
        if (total == 0) throw new IllegalArgumentException("No matching classes");
        System.out.println("Disassembled " + total + " selected classes (including nested classes).");
    }
}
