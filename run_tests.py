#!/usr/bin/env python3
"""
Run every check in the repo:

    python3 run_tests.py            everything (~1-2 min, mostly the OS tests)
    python3 run_tests.py --quick    skip the slow OS tests

Uses the official Nand2Tetris tools in tools/ (needs Java). Anything that
would write into the project folders runs on a temporary copy instead.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
P = ROOT / "projects"
results = []


def tool(name, *args):
    r = subprocess.run(["bash", str(TOOLS / f"{name}.sh"), *map(str, args)],
                       capture_output=True, text=True)
    return (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ""


def check(label, ok, detail=""):
    results.append(ok)
    print(f"  {'ok ' if ok else 'FAIL'} {label}" + (f"  ({detail})" if detail and not ok else ""))


def section(title):
    print(f"\n== {title}")


def tst_passes(tst, emulator):
    last = tool(emulator, tst)
    return "successfully" in last, last


def hardware():
    section("Projects 1-3, 5: HDL chips")
    for proj in ("1", "2", "3/a", "3/b", "5"):
        for tst in sorted((P / proj).glob("*.tst")):
            if tst.name == "Memory.tst":
                continue                      # interactive; headless copy below
            ok, last = tst_passes(tst, "HardwareSimulator")
            check(f"{proj}/{tst.stem}", ok, last)
    # Memory.tst asks a human to hold keys; drop just those two checks.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in ("Memory.hdl", "Memory.cmp", "Memory.tst"):
            shutil.copy(P / "5" / f, tmp)
        t = (tmp / "Memory.tst").read_text()
        t = re.sub(r'echo "[^"]*",', "", t)
        t = re.sub(r"while out <> \d+ \{.*?\}\s*clear-echo,\s*output;", "", t, flags=re.S)
        (tmp / "Memory.tst").write_text(t)
        cmp_lines = (tmp / "Memory.cmp").read_text().splitlines()
        (tmp / "Memory.cmp").write_text("\n".join(
            l for l in cmp_lines if not re.search(r"110000000000000 \|\s+(75|89) \|", l)) + "\n")
        ok, last = tst_passes(tmp / "Memory.tst", "HardwareSimulator")
        check("5/Memory (keyboard steps removed)", ok, last)


def machine_language():
    section("Project 4: Hack assembly")
    for tst in (P / "4/mult/Mult.tst", P / "4/fill/FillAutomatic.tst"):
        ok, last = tst_passes(tst, "CPUEmulator")
        check(tst.stem, ok, last)


def assembler():
    section("Project 6: assembler vs the official one")
    with tempfile.TemporaryDirectory() as tmp:
        for asm in sorted(list((P / "6").glob("*/*.asm")) + list((P / "4").glob("*/*.asm"))):
            work = Path(tmp) / asm.name
            shutil.copy(asm, work)
            tool("Assembler", work)
            expected = work.with_suffix(".hack").read_text().replace("\r", "")
            subprocess.run([sys.executable, P / "6/hack_assembler.py", work], capture_output=True)
            check(asm.name, work.with_suffix(".hack").read_text() == expected)


def vm_translator():
    section("Projects 7-8: VM translator")
    with tempfile.TemporaryDirectory() as tmp:
        for tst in sorted(list((P / "7").glob("*/*/*.tst")) + list((P / "8").glob("*/*/*.tst"))):
            if tst.stem.endswith("VME"):
                continue
            work = Path(tmp) / tst.parent.name
            shutil.copytree(tst.parent, work)
            vm_files = list(work.glob("*.vm"))
            # a whole program (has Sys.vm) is translated as a folder, with bootstrap
            target = work if any(f.stem == "Sys" for f in vm_files) else vm_files[0]
            subprocess.run([sys.executable, P / "8/vm_translator.py", target], capture_output=True)
            ok, last = tst_passes(work / tst.name, "CPUEmulator")
            check(tst.stem, ok, last)


def compiler():
    section("Project 10: syntax analyzer XML")
    with tempfile.TemporaryDirectory() as tmp:
        for d in sorted(p for p in (P / "10").iterdir() if p.is_dir()):
            work = Path(tmp) / d.name
            shutil.copytree(d, work, ignore=shutil.ignore_patterns("output"))
            subprocess.run([sys.executable, P / "10/jack_analyzer.py", work], capture_output=True)
            for jack in work.glob("*.jack"):
                for suffix in ("", "T"):
                    name = f"{jack.stem}{suffix}.xml"
                    last = tool("TextComparer", work / name, work / "output" / name)
                    check(f"{d.name}/{name}", "successfully" in last, last)

    section("Project 11 + 9: everything compiles")
    with tempfile.TemporaryDirectory() as tmp:
        for d in sorted([p for p in (P / "11").iterdir() if p.is_dir()] + [P / "9/Snake"]):
            work = Path(tmp) / d.name
            shutil.copytree(d, work)
            r = subprocess.run([sys.executable, P / "11/jack_compiler.py", work], capture_output=True, text=True)
            check(d.name, r.returncode == 0, r.stderr.strip())


def operating_system():
    section("Project 12: OS (my compiler + my OS, official test scripts)")
    with tempfile.TemporaryDirectory() as tmp:
        osdir = Path(tmp) / "os"
        osdir.mkdir()
        for jack in (P / "12").glob("*.jack"):
            shutil.copy(jack, osdir)
        subprocess.run([sys.executable, P / "11/jack_compiler.py", osdir], capture_output=True)
        for test in ("ArrayTest", "MathTest", "MemoryTest", "MemoryTest/MemoryDiag"):
            src = P / "12" / test
            work = Path(tmp) / src.name
            shutil.copytree(src, work, ignore=shutil.ignore_patterns("MemoryDiag"))
            for vm in osdir.glob("*.vm"):
                shutil.copy(vm, work)
            subprocess.run([sys.executable, P / "11/jack_compiler.py", work / "Main.jack"], capture_output=True)
            tst = work / f"{src.name}.tst"
            # The scripts budget steps for the emulator's fast built-in OS;
            # an OS written in Jack runs as VM code, so give it more time.
            tst.write_text(tst.read_text().replace("repeat 1000000 ", "repeat 15000000 "))
            ok, last = tst_passes(tst, "VMEmulator")
            check(src.name, ok, last)


def breadboard():
    for name, script in (("8-bit computer", "hardware/8bit-computer/tests/test_programs.py"),
                         ("VGA card", "hardware/vga-card/tests/test_vga.py")):
        section(name)
        r = subprocess.run([sys.executable, ROOT / script], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            check(line[4:], line.startswith("ok"))
        if r.returncode:
            check(script, False, r.stderr.strip().splitlines()[-1])


def main():
    if not shutil.which("java"):
        sys.exit("needs Java for the Nand2Tetris tools")
    hardware()
    machine_language()
    assembler()
    vm_translator()
    compiler()
    if "--quick" not in sys.argv:
        operating_system()
    breadboard()
    # The tools save window state into tools/bin/*.dat; don't leave that as a diff.
    subprocess.run(["git", "-C", ROOT, "checkout", "--", "tools/bin"], capture_output=True)
    print(f"\n{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
