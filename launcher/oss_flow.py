"""OSS Flow launcher: buttons for the open-source design and verification flow.

Every button runs the same Makefile target a trainee would type in the
Verification Terminal (the command is shown at the bottom of the window),
so the launcher, the terminal and gvim/vi can be mixed freely.
Uses only the Python standard library (tkinter) that ships in the bundle.
"""
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent.parent
BASH = BUNDLE / "usr" / "bin" / "bash.exe"
GVIM = BUNDLE / "opt" / "gvim" / "vim" / "vim92" / "gvim.exe"
SURFER = BUNDLE / "opt" / "surfer" / "surfer.exe"
TERMINAL_CMD = BUNDLE / "Verification_Terminal.cmd"
EXAMPLES = BUNDLE / "examples"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

COV_KINDS = ("line", "toggle", "branch", "expr", "covergroup")
COV_RE = re.compile(r"^\s*(line|toggle|branch|expr|covergroup)\s*:\s*([\d.]+)%")
TESTS_RE = re.compile(r"^TESTS\s*[:?]?=\s*(.*)$", re.M)
EXAMPLE_INFO = {
    "design_seq_det": "Design flow (Verilog .v): sim, waves, lint, synth, schematic, FSM",
    "counter": "Basic SystemVerilog: tests TC1/TC2, waves, coverage, synth",
    "sv_project": "SystemVerilog verification: tests, SVA, coverage, waves, synth",
    "uvm_project": "UVM verification: UVM tests, coverage, waves, synth",
}
FLOW_NAMES = {"design": "Design flow (Verilog)", "sv": "SystemVerilog verification",
              "uvm": "UVM verification", "basic": "Basic SystemVerilog (TC1, TC2 tests)",
              "make": "Your Makefile (tests and regressions read from it)"}
# targets of a Makefile line "name:" (not "name := value"); simulator-specific variants are hidden
TARGET_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_-]*)\s*:(?!=)", re.M)
SIM_SUFFIX_RE = re.compile(r"_(VCS|Questa|QUESTA|questa|vcs|VERILATOR|Verilator|verilator|IUS|Xcelium|XCELIUM)$")
TEST_TARGET_RE = re.compile(r"(?i)^(tc|test|testcase)_?\d+$")


def tool_env():
    """Same environment as Verification_Terminal.cmd: bundle tools only."""
    env = dict(os.environ)
    sysroot = env.get("SystemRoot", r"C:\Windows")
    env["PATH"] = ";".join([
        str(BUNDLE / "opt" / "surfer"), str(BUNDLE / "opt" / "graphviz" / "bin"),
        str(BUNDLE / "ucrt64" / "bin"), str(BUNDLE / "usr" / "bin"),
        sysroot + r"\System32", sysroot, sysroot + r"\System32\WindowsPowerShell\v1.0"])
    env["MSYSTEM"] = "UCRT64"
    env["CHERE_INVOKING"] = "1"
    env["MSYS2_PATH_TYPE"] = "inherit"
    env["UVM_HOME"] = str(BUNDLE / "opt" / "uvm" / "src").replace("\\", "/")
    env.setdefault("HOME", env.get("USERPROFILE", str(Path.home())))
    return env


ENV = tool_env()


def shq(text):
    return "'" + str(text).replace("'", "'\\''") + "'"


def detect(project):
    """Return (flow, run_dir) for a project folder: design, sv, uvm, basic or make.
    The folder may also be the run folder itself (the one that holds the Makefile, e.g. sim/).
    'make' = any other Makefile (for example a lab Makefile with TC1, regress_12, ...): its own
    targets are used."""
    p = Path(project)
    if (p / "simdir" / "Makefile").exists():
        return "design", p / "simdir"
    if p.name == "simdir" and (p / "Makefile").exists():
        return "design", p
    run_dir = p / "sim" if (p / "sim" / "Makefile").exists() else (p if (p / "Makefile").exists() else None)
    if run_dir is None:
        return None, None
    text = (run_dir / "Makefile").read_text(errors="replace")
    if re.search(r"^TC%:", text, re.M):
        return "basic", run_dir
    if not re.search(r"^run\s*:", text, re.M):
        return "make", run_dir
    if "UVM_HOME" in text:
        return "uvm", run_dir
    return "sv", run_dir


def make_targets(run_dir):
    """User-facing targets of a Makefile in file order: no .PHONY/.SUFFIXES, no file names
    (with a dot), no simulator-specific variants like TC1_VCS or TC1_VERILATOR."""
    names = []
    for name in TARGET_RE.findall(makefile_text(run_dir)):
        if SIM_SUFFIX_RE.search(name) or name in names:
            continue
        names.append(name)
    return names


def make_simulator(run_dir):
    """(extra make argument, Makefile default) for Makefiles with a SIMULATOR switch.
    If the Makefile has *_VERILATOR targets, every call gets SIMULATOR=VERILATOR."""
    text = makefile_text(run_dir)
    m = re.search(r"^SIMULATOR\s*[:?]?=\s*(\S+)", text, re.M)
    if not m:
        return "", ""
    if re.search(r"^\w+_VERILATOR\s*:", text, re.M):
        return "SIMULATOR=VERILATOR", m.group(1)
    return "", m.group(1)


def make_seed_arg(run_dir, test, seed):
    """SEEDn=<seed> for test TCn if the Makefile has SEEDn, else SEED=<seed> if it has SEED, else ''."""
    seed = seed.strip()
    if not seed:
        return ""
    text = makefile_text(run_dir)
    n = re.search(r"(\d+)$", test or "")
    if n and re.search(r"^SEED{}\s*[:?]?=".format(n.group(1)), text, re.M):
        return "SEED{}={}".format(n.group(1), seed)
    if re.search(r"^SEED\s*[:?]?=", text, re.M):
        return "SEED={}".format(seed)
    return ""


def newest_file(folder, patterns, must_contain=None):
    """The most recently changed file in folder matching one of the glob patterns
    (optionally containing a text in its first 4000 characters)."""
    files = [f for pat in patterns for f in Path(folder).glob(pat) if f.is_file()]
    if must_contain:
        files = [f for f in files if must_contain in f.read_text(errors="replace")[:4000]]
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def makefile_text(run_dir):
    mk = Path(run_dir) / "Makefile"
    return mk.read_text(errors="replace") if mk.exists() else ""


def tests_from(run_dir):
    m = TESTS_RE.search(makefile_text(run_dir))
    return m.group(1).split() if m else []


def has_target(run_dir, target):
    return re.search(r"^{}\s*:".format(re.escape(target)), makefile_text(run_dir), re.M) is not None


def shell_command(run_dir, cmd):
    """bash --login -c 'cd <dir> && <cmd>' with the bundle's tools."""
    script = "cd {} && {}".format(shq(str(run_dir).replace("\\", "/")), cmd)
    return [str(BASH), "--login", "-c", script]


def make_command(run_dir, args):
    """bash --login -c 'cd <dir> && make <args>' with the bundle's tools."""
    return shell_command(run_dir, "make --no-print-directory " + args)


def file_kind(path):
    """Verilog / SystemVerilog / UVM, from the extension and the contents."""
    p = Path(path)
    if p.suffix.lower() == ".v":
        return "Verilog"
    try:
        text = p.read_text(errors="replace")
    except OSError:
        text = ""
    return "UVM" if re.search(r"uvm_pkg|uvm_macros|extends\s+uvm_", text) else "SystemVerilog"


KIND_TOOL = {"Verilog": "vrun", "SystemVerilog": "svrun", "UVM": "uvmrun"}


def single_file_command(path, lint=False, extra="", mode="", kind=None):
    """vrun (Verilog), svrun (SystemVerilog/SVA) or uvmrun (UVM) for one file, like 'vcs file.sv -R'.
    mode: '' = compile + simulate, 'compile' = compile only, 'sim' = simulate the last compile."""
    p = Path(path)
    tool = KIND_TOOL[kind or file_kind(p)]
    flag = " --lint" if lint else (" --" + mode if mode else "")
    cmd = "{} {}{}".format(tool, shq(p.name), flag)
    if extra.strip():
        cmd += " " + extra.strip()
    return p.parent, cmd


class Job:
    """A Windows job object: every process started by a run belongs to it, so Stop can end them all.
    (taskkill /T misses MSYS programs, e.g. the simulation that make started.)"""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.nt = ctypes.WinDLL("ntdll")
        self.k.CreateJobObjectW.restype = wintypes.HANDLE
        self.k.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        self.k.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        self.k.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
        self.k.CloseHandle.argtypes = (wintypes.HANDLE,)
        self.nt.NtResumeProcess.argtypes = (wintypes.HANDLE,)
        self.handle = self.k.CreateJobObjectW(None, None)

    def start(self, cmd, **kw):
        """Start cmd suspended, put it in the job, then let it run (no child can escape)."""
        kw["creationflags"] = kw.get("creationflags", 0) | 0x00000004   # CREATE_SUSPENDED
        proc = subprocess.Popen(cmd, **kw)
        if self.handle:
            self.k.AssignProcessToJobObject(self.handle, int(proc._handle))
        self.nt.NtResumeProcess(int(proc._handle))
        return proc

    def kill(self):
        if self.handle:
            self.k.TerminateJobObject(self.handle, 1)

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle)
            self.handle = None


def start_make(run_dir, args, shell=None):
    """Start 'make <args>' (or a shell command) in its own job; returns (process, job)."""
    job = Job()
    cmd = shell_command(run_dir, shell) if shell else make_command(run_dir, args)
    proc = job.start(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     env=ENV, creationflags=NO_WINDOW, text=True, encoding="utf-8", errors="replace")
    return proc, job


def run_make_shell(run_dir, cmd, on_line):
    """Run one shell command (e.g. svrun file.sv) in run_dir, call on_line per line, return exit code."""
    proc, job = start_make(run_dir, "", shell=cmd)
    for line in proc.stdout:
        on_line(line.rstrip("\r\n"))
    rc = proc.wait()
    job.close()
    return rc


def run_make(run_dir, args, on_line):
    """Run one make command, call on_line(text) per output line, return exit code."""
    proc, job = start_make(run_dir, args)
    for line in proc.stdout:
        on_line(line.rstrip("\r\n"))
    rc = proc.wait()
    job.close()
    return rc


def coverage_from(lines):
    found = {}
    for line in lines:
        m = COV_RE.match(line)
        if m:
            found[m.group(1)] = float(m.group(2))
    return found


def line_tag(line):
    low = line.lower()
    if "%error" in low or "assertion failed" in low or "fail" in low or "error:" in low:
        if "uvm_error :    0" not in low and "errors=0" not in low:
            return "bad"
    if "%warning" in low or "warning" in low:
        return "warn"
    if "pass" in low or "created" in low or "completed" in low:
        return "good"
    return ""


def single_starter(name, kind):
    """Small working starter file for the Single file tab (prints something, so the Console shows output)."""
    if kind == "Verilog":
        return ("`timescale 1ns/1ps\n"
                "// {n}.v : Verilog file. Compile and Simulate with vrun (Icarus Verilog).\n"
                "module {n};\n"
                "  reg       clk = 0;\n"
                "  reg [3:0] count = 0;\n\n"
                "  always #5 clk = ~clk;\n"
                "  always @(posedge clk) count <= count + 1;\n\n"
                "  initial begin\n"
                "    $dumpfile(\"dump.vcd\");      // waveform: click Waveform after Simulate\n"
                "    $dumpvars(0, {n});\n"
                "    repeat (8) @(negedge clk) $display(\"time=%0t count=%0d\", $time, count);\n"
                "    $finish;\n"
                "  end\n"
                "endmodule\n").format(n=name)
    if kind == "UVM":
        return ("// {n}.sv : UVM file. Compile once, then Simulate (uvmrun = Verilator + UVM library).\n"
                "// Choose the test with Arguments, e.g. +UVM_TESTNAME={n}_test\n"
                "`include \"uvm_macros.svh\"\n"
                "import uvm_pkg::*;\n\n"
                "class {n}_test extends uvm_test;\n"
                "  `uvm_component_utils({n}_test)\n"
                "  function new(string name, uvm_component parent);\n"
                "    super.new(name, parent);\n"
                "  endfunction\n"
                "  task run_phase(uvm_phase phase);\n"
                "    phase.raise_objection(this);\n"
                "    `uvm_info(\"TEST\", \"Hello from {n}_test\", UVM_LOW)\n"
                "    phase.drop_objection(this);\n"
                "  endtask\n"
                "endclass\n\n"
                "module {n};\n"
                "  initial run_test(\"{n}_test\");\n"
                "endmodule\n").format(n=name)
    return ("// {n}.sv : SystemVerilog file. Compile and Simulate with svrun (Verilator).\n"
            "module {n};\n"
            "  class packet;\n"
            "    rand bit [7:0] addr;\n"
            "    constraint c_addr {{ addr inside {{[10:20]}}; }}\n"
            "  endclass\n\n"
            "  initial begin\n"
            "    static packet p = new();\n"
            "    repeat (5) begin\n"
            "      void'(p.randomize());\n"
            "      $display(\"addr = %0d\", p.addr);\n"
            "    end\n"
            "    $finish;\n"
            "  end\n"
            "endmodule\n").format(n=name)


def module_skeleton(name, is_tb, ext):
    sig = "logic" if ext == ".sv" else "reg"
    wire = "logic" if ext == ".sv" else "wire"
    if is_tb:
        return ("`timescale 1ns/1ps\nmodule {n};\n  {s} clk = 0;\n  always #5 clk = ~clk;\n\n"
                "  initial begin\n    $dumpfile(\"dump.vcd\");\n    $dumpvars(0, {n});\n"
                "    // drive inputs and check outputs here\n    #100;\n"
                "    $display(\"PASS: all checks passed\");\n    $finish;\n  end\nendmodule\n").format(n=name, s=sig)
    return "module {n} (\n  input  {w} clk,\n  input  {w} rst_n\n);\n\nendmodule\n".format(n=name, w=wire)


def file_rule_error(flow, where, ext):
    """The Makefiles find files by extension; refuse combinations they would silently ignore."""
    if flow == "design" and ext != ".v":
        return "The Design flow (Icarus) reads .v files only. Choose .v."
    if flow in ("sv", "uvm", "basic") and where == "tb" and ext != ".sv":
        return "In this flow testbench files must be .sv (the Makefile reads tb/*.sv). Choose .sv."
    return ""


# ------------------------------------------------------------------ coverage reports (HTML)
SECTION_RE = re.compile(r"^(\S.*?):\s*$")
METRIC_RE = re.compile(r"^\s+(\w+)\s*:\s*([\d.]+)%\s*\(\s*(\d+)/\s*(\d+)\)")
CG_RE = re.compile(r"^\s+(\S+)\s*:\s*([\d.]+)%\s*\(\s*(\d+)/\s*(\d+)\)")
CODE_KINDS = ("line", "toggle", "branch", "expr")


def parse_cov_report(text):
    """Split verilator_coverage --report summary,hier output into sections."""
    sections, current, owner = {}, None, None
    for raw in text.splitlines():
        m = SECTION_RE.match(raw)
        if m and not raw.startswith(" "):
            current, owner = m.group(1), None
            sections[current] = []
            continue
        if current is None or not raw.strip():
            continue
        if current == "Covergroup Coverage Summary":
            c = CG_RE.match(raw)
            if c:
                sections[current].append((c.group(1), float(c.group(2)), int(c.group(3)), int(c.group(4))))
            continue
        mm = METRIC_RE.match(raw)
        if mm and current == "Coverage Summary":
            sections[current].append((None, mm.group(1), float(mm.group(2)), int(mm.group(3)), int(mm.group(4))))
        elif mm:
            sections[current].append((owner, mm.group(1), float(mm.group(2)), int(mm.group(3)), int(mm.group(4))))
        else:
            owner = raw.strip()
    return sections


def _bar(pct):
    color = "#1a7f37" if pct >= 90 else ("#b26a00" if pct >= 50 else "#c62828")
    return ('<div class="bar"><div style="width:{:.0f}%;background:{}"></div></div>'
            '<span style="color:{}">{:.1f}%</span>').format(pct, color, color, pct)


def _page(title, body):
    return ("<!doctype html><html><head><meta charset='utf-8'><title>{t}</title><style>"
            "body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;color:#222}}"
            "table{{border-collapse:collapse;margin:8px 0 20px}}td,th{{padding:4px 12px;border-bottom:1px solid #ddd;text-align:left}}"
            ".bar{{display:inline-block;width:140px;height:10px;background:#eee;margin-right:8px;vertical-align:middle}}"
            ".bar div{{height:10px}}.miss{{background:#fdecea}}.note{{color:#666;font-size:13px}}"
            "</style></head><body><h1>{t}</h1>{b}</body></html>").format(t=title, b=body)


def write_coverage_html(run_dir):
    """Create code_coverage.html and functional_coverage.html from cov_report.txt (or cov_summary.txt)."""
    run_dir = Path(run_dir)
    src = run_dir / "cov_report.txt"
    if not src.exists():
        src = run_dir / "cov_summary.txt"
    if not src.exists():
        return None, None
    sec = parse_cov_report(src.read_text(errors="replace"))
    summary = sec.get("Coverage Summary", [])
    rows = "".join("<tr><td>{}</td><td>{}</td><td>{}/{}</td></tr>".format(k, _bar(p), a, b)
                   for _, k, p, a, b in summary if k in CODE_KINDS)
    body = "<h2>Overall code coverage</h2><table><tr><th>Type</th><th>Coverage</th><th>Hit/total</th></tr>{}</table>".format(rows)
    for title in ("Design Unit Coverage Summary", "Hierarchy Coverage Summary"):
        items = [r for r in sec.get(title, []) if r[1] in CODE_KINDS]
        if items:
            body += "<h2>{}</h2><table><tr><th>Module / instance</th><th>Type</th><th>Coverage</th><th>Hit/total</th></tr>".format(
                "Per module (design unit)" if title.startswith("Design") else "Per instance (hierarchy)")
            for owner, k, p, a, b in items:
                body += "<tr{}><td>{}</td><td>{}</td><td>{}</td><td>{}/{}</td></tr>".format(
                    ' class="miss"' if p < 100 else "", owner, k, _bar(p), a, b)
            body += "</table>"
    if (run_dir / "cov_html" / "index.html").exists():
        body += '<p><a href="cov_html/index.html">Line-by-line source view (lcov HTML)</a></p>'
    body += ('<p class="note">Source lines that were never executed are marked %00 in the cov_annot/ folder. '
             'Generated from {}.</p>').format(src.name)
    code = run_dir / "code_coverage.html"
    code.write_text(_page("Code coverage", body), encoding="utf-8")

    cg = sec.get("Covergroup Coverage Summary", [])
    users = [r for r in sec.get("Hierarchy Coverage Summary", []) if r[1] == "user"]
    fbody = ""
    if cg:
        fbody += "<h2>Covergroups, coverpoints and bins</h2><table><tr><th>Name</th><th>Coverage</th><th>Hit/total</th></tr>"
        for name, p, a, b in cg:
            depth = name.count(".")
            fbody += "<tr{}><td style='padding-left:{}px'>{}</td><td>{}</td><td>{}/{}</td></tr>".format(
                ' class="miss"' if p < 100 else "", 12 + 18 * max(depth - 1, 0), name, _bar(p), a, b)
        fbody += "</table>"
    covers = [r for r in users if "." in (r[0] or "") and r[0].split(".")[-1].startswith(("c_", "cov", "cp_"))] or users
    if covers:
        fbody += ("<h2>Assertion cover properties (user)</h2><table><tr><th>Instance / cover</th><th>Coverage</th>"
                  "<th>Hit/total</th></tr>")
        for owner, k, p, a, b in covers:
            fbody += "<tr{}><td>{}</td><td>{}</td><td>{}/{}</td></tr>".format(
                ' class="miss"' if p < 100 else "", owner, _bar(p), a, b)
        fbody += "</table>"
    if not fbody:
        fbody = "<p>No functional coverage found. Add covergroups (and SVA cover properties) to your testbench.</p>"
    fbody += '<p class="note">Bins that were never hit are shaded red. Details per bin: cov_covergroup/ folder.</p>'
    func = run_dir / "functional_coverage.html"
    func.write_text(_page("Functional coverage", fbody), encoding="utf-8")
    return code, func


# ------------------------------------------------------------------ result tabs: data helpers
VCD_MAX_BYTES = 60 * 1024 * 1024


def parse_vcd(path):
    """Read a VCD file. Returns {'timescale', 'end', 'signals': [{name, width, id}], 'changes': {id: (times, values)}}."""
    path = Path(path)
    if path.stat().st_size > VCD_MAX_BYTES:
        raise ValueError("{} is {:.0f} MB; the built-in viewer reads up to {:.0f} MB. Use 'Open in Surfer'.".format(
            path.name, path.stat().st_size / 1e6, VCD_MAX_BYTES / 1e6))
    text = path.read_text(errors="replace")
    head, sep, body = text.partition("$enddefinitions")
    if not sep:
        raise ValueError("{} is not a VCD file (no $enddefinitions)".format(path.name))
    toks = head.split()
    signals, scope, timescale, i = [], [], "", 0
    while i < len(toks):
        t = toks[i]
        if t == "$scope" and i + 2 < len(toks):
            scope.append(toks[i + 2]); i += 3
        elif t == "$upscope":
            if scope:
                scope.pop()
            i += 1
        elif t == "$timescale":
            j = i + 1
            while j < len(toks) and toks[j] != "$end":
                timescale += toks[j]; j += 1
            i = j
        elif t == "$var" and i + 4 < len(toks):
            width, vid, ref = toks[i + 2], toks[i + 3], toks[i + 4]
            rng = toks[i + 5] if i + 5 < len(toks) and toks[i + 5].startswith("[") else ""
            signals.append({"name": ".".join(scope + [ref + rng]), "width": int(width) if width.isdigit() else 1,
                            "id": vid})
            i += 5
        else:
            i += 1
    changes = {s["id"]: ([], []) for s in signals}
    btoks = body.split()
    t, end, k = 0, 0, 1   # skip the "$end" that closes $enddefinitions
    while k < len(btoks):
        tok = btoks[k]
        c = tok[0]
        if c == "#":
            try:
                t = int(tok[1:]); end = max(end, t)
            except ValueError:
                pass
        elif c in "bBrR" and k + 1 < len(btoks):
            vid = btoks[k + 1]; k += 1
            if vid in changes:
                tl, vl = changes[vid]
                if not vl or vl[-1] != tok[1:] or tl[-1] != t:
                    tl.append(t); vl.append(tok[1:])
        elif c in "01xXzZuU-":
            vid = tok[1:]
            if vid in changes:
                tl, vl = changes[vid]
                tl.append(t); vl.append(c.lower())
        elif tok == "$comment":
            while k < len(btoks) and btoks[k] != "$end":
                k += 1
        k += 1
    return {"timescale": timescale or "1s", "end": end, "signals": signals, "changes": changes}


def vcd_value_at(times, values, t):
    import bisect
    i = bisect.bisect_right(times, t) - 1
    return values[i] if i >= 0 else "x"


def fmt_vcd_value(v, width):
    if width <= 1 or not v:
        return v
    if set(v) <= {"0", "1"}:
        return "{:X}".format(int(v, 2))
    if "x" in v or "z" in v:
        return v if len(v) <= 8 else ("x" if "x" in v else "z")
    return v


def coverage_tree(text):
    """Rows (iid, parent, label, pct, hit, total) for the Coverage tab, from cov_report.txt or cov_summary.txt."""
    sec = parse_cov_report(text)
    rows, seen = [], set()

    def add(iid, parent, label, pct=None, hit=None, tot=None):
        if iid not in seen:
            seen.add(iid)
            rows.append((iid, parent, label, pct, hit, tot))
    summ = sec.get("Coverage Summary", [])
    add("code", "", "Code coverage (overall)")
    for _, k, p, a, b in summ:
        if k in CODE_KINDS:
            add("code/" + k, "code", k, p, a, b)
    for title, key, label in (("Design Unit Coverage Summary", "mod", "Code coverage per module"),
                              ("Hierarchy Coverage Summary", "inst", "Code coverage per instance")):
        items = [r for r in sec.get(title, []) if r[1] in CODE_KINDS]
        if items:
            add(key, "", label)
            for owner, k, p, a, b in items:
                add("{}/{}".format(key, owner), key, owner)
                add("{}/{}/{}".format(key, owner, k), "{}/{}".format(key, owner), k, p, a, b)
    cg_total = [r for r in summ if r[1] == "covergroup"]
    cg = sec.get("Covergroup Coverage Summary", [])
    if cg or cg_total:
        p, a, b = (cg_total[0][2], cg_total[0][3], cg_total[0][4]) if cg_total else (None, None, None)
        add("func", "", "Functional coverage (covergroups, coverpoints, bins)", p, a, b)
        names = []
        for name, p, a, b in cg:
            parent = "func"
            for prev in sorted(names, key=len, reverse=True):
                if name.startswith(prev + "."):
                    parent = "cg/" + prev
                    break
            label = name if parent == "func" else name[len(parent) - 3 + 1:]
            add("cg/" + name, parent, label, p, a, b)
            names.append(name)
    users = [r for r in sec.get("Hierarchy Coverage Summary", []) if r[1] == "user" and r[0] and "." in r[0]]
    if users:
        add("asrt", "", "Assertion cover properties")
        for owner, k, p, a, b in users:
            add("asrt/" + owner, "asrt", owner, p, a, b)
    return rows


DOT_DPI = 80     # Graphviz picture resolution; gui() raises it on high-DPI screens


def make_dpi_aware():
    """Tell Windows this program draws itself at the real screen resolution. Without this, Windows draws
    the window at 100 % and stretches the picture (125 %, 150 %, ... display scaling), which looks blurry."""
    if sys.platform != "win32":
        return
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)        # system DPI aware (Windows 8.1 and later)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()          # older Windows
        except Exception:
            pass


def render_dot_png(dot_path):
    """Draw a Graphviz .dot file as PNG next to it (for the Schematic / FSM tabs). Returns the PNG path."""
    dot_path = Path(dot_path)
    png = dot_path.with_suffix(".png")
    if not png.exists() or png.stat().st_mtime < dot_path.stat().st_mtime:
        exe = BUNDLE / "opt" / "graphviz" / "bin" / "dot.exe"
        r = subprocess.run([str(exe), "-Tpng", "-Gdpi={}".format(DOT_DPI), str(dot_path), "-o", str(png)], env=ENV,
                           creationflags=NO_WINDOW, capture_output=True, text=True)
        if r.returncode != 0 or not png.exists():
            raise RuntimeError("Graphviz could not draw {}: {}".format(dot_path.name, r.stderr.strip()[:300]))
    return png


# ------------------------------------------------------------------ GUI
def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    make_dpi_aware()
    root = tk.Tk()
    root.title("OSS Flow: design and verification")
    try:      # window + taskbar icon, also used by every dialog of this program
        root.iconbitmap(default=str(Path(__file__).resolve().parent / "oss_flow.ico"))
    except tk.TclError:
        pass
    # Screen scaling: 1.0 at 100 %, 1.5 at 150 % ... Fonts follow by themselves; pixel sizes use px().
    UI = max(1.0, root.winfo_fpixels("1i") / 96.0)

    def px(n):
        return int(round(n * UI))
    global DOT_DPI
    DOT_DPI = px(80)
    ttk.Style(root).configure("Treeview", rowheight=px(22))
    root.geometry("{}x{}".format(px(1150), px(820)))
    if root.winfo_screenheight() < px(900) or root.winfo_screenwidth() < px(1200):
        root.state("zoomed")      # small screens: use the whole screen for the result tabs
    state = {"project": None, "flow": None, "run": None, "proc": None, "lines": []}
    q = queue.Queue()

    proj_var = tk.StringVar(value="(no project yet: Browse or New project)")
    flow_var = tk.StringVar(value="")
    test_var = tk.StringVar()
    seed_var = tk.StringVar(value="1")
    verb_var = tk.StringVar(value="UVM_MEDIUM")
    waves_var = tk.BooleanVar(value=False)
    fmt_var = tk.StringVar(value="vcd")
    reg_var = tk.StringVar()        # 'Your Makefile' projects: regression target
    target_var = tk.StringVar()     # 'Your Makefile' projects: any other target
    cmd_var = tk.StringVar(value="Command used: -")
    status_var = tk.StringVar(value="Ready")
    cov_vars = {k: tk.StringVar(value="-") for k in COV_KINDS}

    # pop-ups always belong to the main window, so they open on top of it
    def info(msg):
        messagebox.showinfo("OSS Flow", msg, parent=root)

    def warn(msg):
        messagebox.showwarning("OSS Flow", msg, parent=root)

    def dialog(title):
        win = tk.Toplevel(root)
        win.title(title)
        win.transient(root)
        win.resizable(False, False)
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
        win.update_idletasks()
        win.geometry("+{}+{}".format(root.winfo_rootx() + 120, root.winfo_rooty() + 90))
        win.lift()
        win.grab_set()
        win.focus_force()
        return win, frame

    # Two tabs: "Single file" (quick exercises, like vcs/qrun on one file) and "Project" (Makefile flows)
    tabs = ttk.Notebook(root)
    tabs.pack(fill="x", padx=8, pady=(8, 0))
    single = ttk.Frame(tabs, padding=10)
    ptab = ttk.Frame(tabs, padding=(4, 6))
    tabs.add(single, text="  Single file  ")
    tabs.add(ptab, text="  Project  ")

    def fit_top(*_):
        # the top area takes only the height of the selected tab, so the result tabs get the rest
        root.update_idletasks()
        sel = root.nametowidget(tabs.select())
        tabs.configure(height=sel.winfo_reqheight())
    tabs.bind("<<NotebookTabChanged>>", lambda e: (fit_top(), show_panel()))

    args_var = tk.StringVar(value="")
    file_var = tk.StringVar(value="(no file yet: click New file... or Choose file...)")
    kind_var = tk.StringVar(value="SystemVerilog")
    srow1 = ttk.Frame(single)
    srow1.pack(fill="x")
    ttk.Button(srow1, text="New file...", command=lambda: new_single()).pack(side="left")
    ttk.Button(srow1, text="Choose file...", command=lambda: choose_single()).pack(side="left", padx=6)
    ttk.Label(srow1, textvariable=file_var, font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
    ttk.Label(srow1, text="Type").pack(side="left", padx=(16, 4))
    ttk.Combobox(srow1, textvariable=kind_var, values=["Verilog", "SystemVerilog", "UVM"], width=14,
                 state="readonly").pack(side="left")
    ttk.Label(srow1, text="Verilog = vrun (Icarus) | SystemVerilog = svrun | UVM = uvmrun",
              foreground="#555555").pack(side="left", padx=8)
    srow2 = ttk.Frame(single)
    srow2.pack(fill="x", pady=(10, 0))
    for text, cmd in (("Edit", lambda: single_edit()), ("Compile", lambda: single_run("compile")),
                      ("Simulate", lambda: single_run("sim")), ("Lint", lambda: single_run("lint")),
                      ("Waveform", lambda: single_waveform()), ("Coverage", lambda: single_coverage())):
        ttk.Button(srow2, text=text, width=12, command=cmd).pack(side="left", padx=(0, 6))
    ttk.Button(srow2, text="Terminal here", width=14,
               command=lambda: terminal_here(Path(state["single"]).parent if state.get("single") else None)
               ).pack(side="left", padx=(12, 0))
    srow3 = ttk.Frame(single)
    srow3.pack(fill="x", pady=(10, 0))
    ttk.Label(srow3, text="Arguments").pack(side="left")
    ttk.Entry(srow3, textvariable=args_var, width=44).pack(side="left", padx=6)
    ttk.Label(srow3, text="optional, e.g. +UVM_TESTNAME=my_test   --waves   --cov", foreground="#555555").pack(side="left")
    ttk.Label(single, foreground="#555555", justify="left", text=(
        "Steps: New file (or Choose file) -> write the code in gvim and save (Ctrl+S) -> Compile -> Simulate -> Waveform / Coverage."
        "  Choose the testbench file (initial with $display, or the UVM top).\n"
        "Several files: use the terminal, e.g.  svrun counter.sv counter_tb.sv   or   uvmrun my_if.sv my_pkg.sv top.sv")
              ).pack(anchor="w", pady=(10, 0))

    top = ttk.Frame(ptab)
    top.pack(fill="x", padx=4)
    ttk.Label(top, text="Project").pack(side="left")
    ttk.Entry(top, textvariable=proj_var, state="readonly").pack(side="left", fill="x", expand=True, padx=6)
    ttk.Button(top, text="Browse", command=lambda: browse()).pack(side="left")
    ttk.Button(top, text="New project", command=lambda: new_project()).pack(side="left", padx=4)
    ttk.Button(top, text="Terminal here", command=lambda: terminal_here()).pack(side="left")
    ttk.Label(ptab, textvariable=flow_var, padding=(6, 4)).pack(anchor="w")

    body = ttk.Frame(ptab, padding=(4, 0))
    body.pack(fill="x")
    write_row = ttk.LabelFrame(body, text="1. Write code (opens gvim; save with Ctrl+S, then click a Run button)", padding=6)
    run_row = ttk.LabelFrame(body, text="2. Run", padding=6)
    res_row = ttk.LabelFrame(body, text="3. Results", padding=6)
    for frame in (write_row, run_row, res_row):
        frame.pack(fill="x", pady=3)
    opts_row = ttk.Frame(run_row)
    btn_row = ttk.Frame(run_row)
    cov_row = ttk.Frame(res_row)
    res_btn_row = ttk.Frame(res_row)

    bottom = ttk.Frame(root, padding=8)
    bottom.pack(side="bottom", fill="x")
    clean_text = tk.StringVar(value="Clean file outputs")
    theme_text = tk.StringVar(value="Dark console")

    def make_results():
        # ---- result tabs below the buttons: Console, Log, Report, Coverage, Schematic, FSM, Waveform
        outtabs = ttk.Notebook(root)
        # packed by show_panel()

        def text_tab(title, with_bar=True):
            frame = ttk.Frame(outtabs)
            bar = ttk.Frame(frame)
            if with_bar:
                bar.pack(fill="x", pady=2)
            txt = tk.Text(frame, wrap="none", font=("Consolas", 10))
            ys = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
            xs = ttk.Scrollbar(frame, orient="horizontal", command=txt.xview)
            txt.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
            xs.pack(side="bottom", fill="x")
            ys.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)
            for tag, col in (("good", "#1a7f37"), ("bad", "#c62828"), ("warn", "#b26a00"), ("cmd", "#555555")):
                txt.tag_configure(tag, foreground=col)
            outtabs.add(frame, text="  {}  ".format(title))
            return frame, bar, txt

        con_f, _, out = text_tab("Console", with_bar=False)
        viewers = {}
        for key, title in (("log", "Log"), ("report", "Report")):
            frame, bar, txt = text_tab(title)
            var = tk.StringVar(value="Nothing loaded yet. It fills in after a run (or click 'Open log' / a report button).")
            ttk.Label(bar, textvariable=var).pack(side="left", padx=4)
            viewers[key] = {"frame": frame, "txt": txt, "var": var, "path": None}
            ttk.Button(bar, text="Open in gvim", command=lambda k=key: viewers[k]["path"] and subprocess.Popen(
                [str(GVIM), str(viewers[k]["path"])], env=ENV)).pack(side="right", padx=2)
            ttk.Button(bar, text="Reload", command=lambda k=key: viewers[k]["path"] and show_text(
                k, viewers[k]["path"])).pack(side="right", padx=2)

        def show_text(key, path, select=True):
            v = viewers[key]
            path = Path(path)
            if not path.exists():
                v["var"].set("{} does not exist yet. Run the step that creates it first.".format(path.name))
                if select:
                    outtabs.select(v["frame"])
                return
            data = path.read_text(errors="replace")
            if len(data) > 3_000_000:
                data = "... (only the last 3 MB shown; 'Open in gvim' shows everything)\n" + data[-3_000_000:]
            t = v["txt"]
            t.configure(state="normal")
            t.delete("1.0", "end")
            for line in data.splitlines():
                t.insert("end", line + "\n", line_tag(line))
            v["path"] = path
            v["var"].set("{}   ({})".format(path.name, path.parent))
            if select:
                outtabs.select(v["frame"])

        # Coverage tab: code coverage + functional coverage tree
        cov_f = ttk.Frame(outtabs)
        outtabs.add(cov_f, text="  Coverage  ")
        cov_bar = ttk.Frame(cov_f)
        cov_bar.pack(fill="x", pady=2)
        cov_src = tk.StringVar(value="No coverage yet. Project: run tests, then click Coverage. "
                                     "Single file: put --cov in Arguments, Compile and Simulate, then Coverage.")
        ttk.Label(cov_bar, textvariable=cov_src).pack(side="left", padx=4)
        cov_tree = ttk.Treeview(cov_f, columns=("pct", "bar", "hit"), show="tree headings")
        cov_tree.heading("#0", text="Item")
        cov_tree.heading("pct", text="Coverage")
        cov_tree.heading("bar", text="")
        cov_tree.heading("hit", text="Hit / total")
        cov_tree.column("#0", width=px(420))
        cov_tree.column("pct", width=90, anchor="e")
        cov_tree.column("bar", width=px(130))
        cov_tree.column("hit", width=px(110), anchor="e")
        cov_tree.tag_configure("good", foreground="#1a7f37")
        cov_tree.tag_configure("mid", foreground="#b26a00")
        cov_tree.tag_configure("low", foreground="#c62828")
        cov_ys = ttk.Scrollbar(cov_f, orient="vertical", command=cov_tree.yview)
        cov_tree.configure(yscrollcommand=cov_ys.set)
        cov_ys.pack(side="right", fill="y")
        cov_tree.pack(fill="both", expand=True)
        cov_state = {"dir": None, "annot": None}

        def cov_html():
            if state.get("run") and cov_state["dir"] == state["run"]:
                run("covhtml", lambda: open_default(state["run"] / "cov_html" / "index.html"))
            else:
                info("The line-by-line HTML page is made in projects (button Coverage, then this button).")

        ttk.Button(cov_bar, text="Line-by-line HTML (browser)", command=cov_html).pack(side="right", padx=2)
        ttk.Button(cov_bar, text="Uncovered lines (folder)", command=lambda: cov_state["annot"] and open_default(
            cov_state["annot"])).pack(side="right", padx=2)

        def show_coverage(path, select=True):
            path = Path(path)
            if not path.exists():
                cov_src.set("{} not found. Run tests (and Coverage) first.".format(path.name))
                if select:
                    outtabs.select(cov_f)
                return
            cov_tree.delete(*cov_tree.get_children())
            for iid, parent, label, pct, hit, tot in coverage_tree(path.read_text(errors="replace")):
                vals = ("", "", "")
                tags = ()
                if pct is not None:
                    n = int(round(pct / 10))
                    vals = ("{:.1f}%".format(pct), "█" * n + "░" * (10 - n), "{} / {}".format(hit, tot))
                    tags = ("good",) if pct >= 90 else (("mid",) if pct >= 50 else ("low",))
                cov_tree.insert(parent, "end", iid=iid, text=label, values=vals, tags=tags,
                                open=parent in ("", "code", "func"))
            cov_state["dir"] = path.parent
            annot = [d for d in (path.parent / "cov_annot", path.parent / (path.name.replace("_cov_report.txt", "") + "_cov_annot"),
                                 path.parent / (path.stem + "_annot"))
                     if d.exists()]
            cov_state["annot"] = annot[0] if annot else None
            cov_src.set("{}   ({})".format(path.name, path.parent))
            if select:
                outtabs.select(cov_f)

        # Schematic and FSM tabs: Graphviz drawings shown as images
        def image_tab(title, choices):
            frame = ttk.Frame(outtabs)
            outtabs.add(frame, text="  {}  ".format(title))
            bar = ttk.Frame(frame)
            bar.pack(fill="x", pady=2)
            view = {"frame": frame, "var": tk.StringVar(value="Nothing drawn yet. Design flow project: click the "
                                                                   "{} button.".format(title)),
                    "zoom": tk.StringVar(value="100%"), "which": tk.StringVar(value=choices[0] if choices else ""),
                    "full": None, "img": None, "dot": None}
            if len(choices) > 1:
                cb = ttk.Combobox(bar, textvariable=view["which"], values=choices, width=16, state="readonly")
                cb.pack(side="left", padx=4)
                cb.bind("<<ComboboxSelected>>", lambda e: schematic_choice())
            ttk.Label(bar, text="Zoom").pack(side="left", padx=(8, 2))
            zb = ttk.Combobox(bar, textvariable=view["zoom"], values=["100%", "50%", "25%"], width=6, state="readonly")
            zb.pack(side="left")
            zb.bind("<<ComboboxSelected>>", lambda e: apply_zoom(view))
            ttk.Label(bar, textvariable=view["var"]).pack(side="left", padx=8)
            ttk.Button(bar, text="Open in browser", command=lambda: view["dot"] and open_default(
                Path(view["dot"]).with_suffix(".svg"))).pack(side="right", padx=2)
            canvas = tk.Canvas(frame, background="white")
            ys = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            xs = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
            canvas.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
            xs.pack(side="bottom", fill="x")
            ys.pack(side="right", fill="y")
            canvas.pack(fill="both", expand=True)
            view["canvas"] = canvas
            return view

        def apply_zoom(view):
            if view["full"] is None:
                return
            f = {"100%": 1, "50%": 2, "25%": 4}[view["zoom"].get()]
            view["img"] = view["full"] if f == 1 else view["full"].subsample(f)
            c = view["canvas"]
            c.delete("all")
            c.create_image(0, 0, anchor="nw", image=view["img"])
            c.configure(scrollregion=(0, 0, view["img"].width(), view["img"].height()))

        def show_image(view, dot_path, select=True):
            dot_path = Path(dot_path)
            if select:
                outtabs.select(view["frame"])
            if not dot_path.exists():
                view["var"].set("{} not found. Run the step first.".format(dot_path.name))
                return
            try:
                png = render_dot_png(dot_path)
            except RuntimeError as exc:
                view["var"].set(str(exc))
                return
            view["full"] = tk.PhotoImage(file=str(png))
            view["dot"] = dot_path
            root.update_idletasks()
            w = view["canvas"].winfo_width() or 800
            view["zoom"].set("100%" if view["full"].width() <= w * 1.3 else ("50%" if view["full"].width() <= w * 2.6 else "25%"))
            apply_zoom(view)
            view["var"].set("{}   ({} x {} px)".format(dot_path.name, view["full"].width(), view["full"].height()))

        sch_view = image_tab("Schematic", ["RTL schematic", "Gate schematic"])
        fsm_view = image_tab("FSM", [])

        def schematic_choice():
            if state.get("flow") != "design":
                return
            suffix = "_rtl.dot" if sch_view["which"].get().startswith("RTL") else "_synth.dot"
            show_image(sch_view, state["run"] / (top_name() + suffix))

        # Waveform tab: built-in VCD viewer
        wv_f = ttk.Frame(outtabs)
        outtabs.add(wv_f, text="  Waveform  ")
        wbar = ttk.Frame(wv_f)
        wbar.pack(fill="x", pady=2)
        wv_file = tk.StringVar(value="No waveform loaded. Simulate with 'Save waveform' (VCD), then click Waveform.")
        wv_cur = tk.StringVar(value="")
        wv = {"data": None, "shown": [], "t0": 0.0, "scale": 1.0, "cursor": None, "path": None, "sel": None,
              "unit_ps": 1.0}
        NAME_W, VAL_W, ROW_H, TOP_H = px(210), px(90), px(26), px(26)
        for text, cmd in (("Open VCD...", lambda: wv_open()), ("Zoom in", lambda: wv_zoom(2.0)),
                          ("Zoom out", lambda: wv_zoom(0.5)), ("Fit", lambda: wv_fit()),
                          ("Open in Surfer", lambda: wv["path"] and subprocess.Popen(
                              [str(SURFER), str(wv["path"])], cwd=str(Path(wv["path"]).parent), env=ENV))):
            ttk.Button(wbar, text=text, command=cmd).pack(side="left", padx=2)
        ttk.Label(wbar, textvariable=wv_cur, foreground="#c62828").pack(side="left", padx=8)
        ttk.Label(wbar, textvariable=wv_file).pack(side="left", padx=4)
        wpane = ttk.PanedWindow(wv_f, orient="horizontal")
        wpane.pack(fill="both", expand=True)
        wleft = ttk.Frame(wpane, width=px(240))
        wright = ttk.Frame(wpane)
        wpane.add(wleft, weight=0)
        wpane.add(wright, weight=1)
        wfilter = tk.StringVar(value="")
        ttk.Label(wleft, text="Signals (filter):").pack(anchor="w")
        ttk.Entry(wleft, textvariable=wfilter).pack(fill="x")
        wlist = tk.Listbox(wleft, selectmode="extended", font=("Consolas", 9), exportselection=False)
        wlist.pack(fill="both", expand=True)
        wbtns = ttk.Frame(wleft)
        wbtns.pack(fill="x")
        ttk.Button(wbtns, text="Add >", command=lambda: wv_add()).pack(side="left", fill="x", expand=True)
        ttk.Button(wbtns, text="Remove", command=lambda: wv_remove()).pack(side="left", fill="x", expand=True)
        wcanvas = tk.Canvas(wright, background="white", highlightthickness=0)
        wvs = ttk.Scrollbar(wright, orient="vertical", command=wcanvas.yview)
        whs = ttk.Scrollbar(wright, orient="horizontal", command=lambda *a: wv_hscroll(*a))
        wcanvas.configure(yscrollcommand=wvs.set)
        whs.pack(side="bottom", fill="x")
        wvs.pack(side="right", fill="y")
        wcanvas.pack(fill="both", expand=True)

        def wv_time(t):
            ps = t * wv["unit_ps"]
            for div, unit in ((1e6, "us"), (1e3, "ns"), (1, "ps")):
                if abs(ps) >= div or unit == "ps":
                    return "{:g} {}".format(round(ps / div, 3), unit)

        def wv_names():
            f = wfilter.get().strip().lower()
            return [s for s in wv["data"]["signals"] if f in s["name"].lower()] if wv["data"] else []

        def wv_fill_list(*_):
            wlist.delete(0, "end")
            for s in wv_names():
                wlist.insert("end", s["name"])

        wfilter.trace_add("write", wv_fill_list)
        wlist.bind("<Double-Button-1>", lambda e: wv_add())

        def wv_add():
            names = wv_names()
            for i in wlist.curselection():
                s = names[i]
                if s not in wv["shown"]:
                    wv["shown"].append(s)
            wv_draw()

        def wv_remove():
            if wv["sel"] is not None and wv["sel"] < len(wv["shown"]):
                wv["shown"].pop(wv["sel"])
                wv["sel"] = None
                wv_draw()
            else:
                info("Click a signal name in the waveform first, then Remove.")

        def wv_load(path, select=True):
            path = Path(path)
            if select:
                outtabs.select(wv_f)
            if path.suffix.lower() == ".fst":
                wv_file.set("{}: FST files open in Surfer (the built-in viewer reads VCD).".format(path.name))
                subprocess.Popen([str(SURFER), str(path)], cwd=str(path.parent), env=ENV)
                return
            try:
                d = parse_vcd(path)
            except (ValueError, OSError) as exc:
                wv_file.set(str(exc))
                return
            m = re.match(r"(\d+)\s*([munpf]?s)", d["timescale"])
            mult = {"s": 1e12, "ms": 1e9, "us": 1e6, "ns": 1e3, "ps": 1.0, "fs": 1e-3}
            wv["unit_ps"] = int(m.group(1)) * mult.get(m.group(2), 1.0) if m else 1.0
            keep = [s["name"] for s in wv["shown"]] if wv["path"] == path else []
            wv.update(data=d, path=path, cursor=None, sel=None)
            sigs = d["signals"]
            if keep:
                wv["shown"] = [s for s in sigs if s["name"] in keep]
            else:
                depth = min((s["name"].count(".") for s in sigs), default=0)
                top = [s for s in sigs if s["name"].count(".") == depth]
                wv["shown"] = (top if len(top) >= 3 else sigs)[:20]
            wfilter.set("")
            wv_fill_list()
            wv_file.set("{}   ({} signals, end {})".format(path.name, len(sigs), wv_time(d["end"])))
            root.update_idletasks()
            wv_fit()

        def wv_open():
            start = Path(wv["path"]).parent if wv["path"] else (state.get("run") or Path(ENV["HOME"]))
            f = filedialog.askopenfilename(parent=root, title="Open a waveform", initialdir=str(start),
                                           filetypes=[("VCD waveform", "*.vcd"), ("FST (opens in Surfer)", "*.fst")])
            if f:
                wv_load(f)

        def wv_span():
            return max(wcanvas.winfo_width() - NAME_W - VAL_W - 10, 100) / wv["scale"]

        def wv_clamp():
            end = max(wv["data"]["end"], 1) if wv["data"] else 1
            wv["t0"] = min(max(wv["t0"], 0.0), max(end - wv_span(), 0.0))

        def wv_fit():
            if not wv["data"]:
                return
            wv["scale"] = max(wcanvas.winfo_width() - NAME_W - VAL_W - 10, 100) / max(wv["data"]["end"], 1)
            wv["t0"] = 0.0
            wv_draw()

        def wv_zoom(f, center=None):
            if not wv["data"]:
                return
            span = wv_span()
            c = center if center is not None else wv["t0"] + span / 2
            wv["scale"] = min(wv["scale"] * f, 400.0)
            wv["t0"] = c - (c - wv["t0"]) / f
            wv_clamp()
            wv_draw()

        def wv_hscroll(*a):
            if not wv["data"]:
                return
            end = max(wv["data"]["end"], 1)
            if a[0] == "moveto":
                wv["t0"] = float(a[1]) * end
            elif a[0] == "scroll":
                step = wv_span() * (0.9 if a[2] == "pages" else 0.1)
                wv["t0"] += int(a[1]) * step
            wv_clamp()
            wv_draw()

        def nice_step(x):
            import math
            p = 10 ** math.floor(math.log10(max(x, 1e-12)))
            for m in (1, 2, 5, 10):
                if m * p >= x:
                    return m * p
            return 10 * p

        def wv_draw(*_):
            import bisect
            c = wcanvas
            c.delete("all")
            d = wv["data"]
            if not d:
                c.create_text(20, 20, anchor="nw", text="No waveform loaded.", fill="#555555")
                return
            W = max(c.winfo_width(), 400)
            x0 = NAME_W + VAL_W
            scale, t0 = wv["scale"], wv["t0"]
            span = wv_span()
            t1 = t0 + span
            end = max(d["end"], 1)
            step = nice_step(span / 8)
            t = (int(t0 // step) + 1) * step
            while t < t1:
                x = x0 + (t - t0) * scale
                c.create_line(x, TOP_H - 6, x, TOP_H + len(wv["shown"]) * ROW_H, fill="#eeeeee")
                c.create_text(x, 4, anchor="n", text=wv_time(t), font=("Segoe UI", 8), fill="#555555")
                t += step
            c.create_line(0, TOP_H - 2, W, TOP_H - 2, fill="#cccccc")
            c.create_text(4, 4, anchor="nw", text="Signal", font=("Segoe UI", 8, "bold"))
            c.create_text(NAME_W + 4, 4, anchor="nw", text="Value @ cursor", font=("Segoe UI", 8, "bold"))
            for i, s in enumerate(wv["shown"]):
                y = TOP_H + i * ROW_H
                yh, yl = y + px(5), y + ROW_H - px(5)
                ym = (yh + yl) / 2
                if wv["sel"] == i:
                    c.create_rectangle(0, y, NAME_W, y + ROW_H, fill="#dbeafe", outline="")
                short = ".".join(s["name"].split(".")[-2:])
                c.create_text(4, ym, anchor="w", text=short, font=("Consolas", 9))
                times, vals = d["changes"][s["id"]]
                if wv["cursor"] is not None and times:
                    c.create_text(NAME_W + 4, ym, anchor="w", font=("Consolas", 9), fill="#c62828",
                                  text=fmt_vcd_value(vcd_value_at(times, vals, wv["cursor"]), s["width"]))
                if not times:
                    continue
                k = max(bisect.bisect_right(times, t0) - 1, 0)
                while k < len(times) and times[k] <= t1:
                    ta = max(times[k], t0)
                    tb = min(times[k + 1] if k + 1 < len(times) else end, t1)
                    if tb >= ta:
                        xa, xb = x0 + (ta - t0) * scale, x0 + (tb - t0) * scale
                        v = vals[k]
                        if s["width"] == 1:
                            if v == "1":
                                c.create_line(xa, yh, xb, yh, fill="#1a7f37", width=2)
                            elif v == "0":
                                c.create_line(xa, yl, xb, yl, fill="#1a7f37", width=2)
                            else:
                                c.create_line(xa, ym, xb, ym, fill="#c62828" if v == "x" else "#b26a00", width=2)
                            if k > 0 and times[k] >= t0:
                                c.create_line(xa, yh, xa, yl, fill="#1a7f37")
                        else:
                            col = "#c62828" if ("x" in v or "z" in v) else "#1d4ed8"
                            c.create_line(xa + 2, yh, xb, yh, fill=col)
                            c.create_line(xa + 2, yl, xb, yl, fill=col)
                            c.create_line(xa, ym, xa + 2, yh, fill=col)
                            c.create_line(xa, ym, xa + 2, yl, fill=col)
                            txt = fmt_vcd_value(v, s["width"])
                            if xb - xa > 7 * len(txt) + 8:
                                c.create_text((xa + xb) / 2, ym, text=txt, font=("Consolas", 8), fill=col)
                    k += 1
            if wv["cursor"] is not None and t0 <= wv["cursor"] <= t1:
                x = x0 + (wv["cursor"] - t0) * scale
                c.create_line(x, TOP_H - 6, x, TOP_H + len(wv["shown"]) * ROW_H, fill="#c62828", dash=(4, 2))
            c.configure(scrollregion=(0, 0, W, TOP_H + len(wv["shown"]) * ROW_H + 10))
            whs.set(t0 / end, min(1.0, t1 / end))

        def wv_click(e):
            if not wv["data"]:
                return
            y = wcanvas.canvasy(e.y)
            if e.x < NAME_W:
                row = int((y - TOP_H) // ROW_H)
                wv["sel"] = row if 0 <= row < len(wv["shown"]) else None
            elif e.x > NAME_W + VAL_W:
                wv["cursor"] = wv["t0"] + (e.x - NAME_W - VAL_W) / wv["scale"]
                wv_cur.set("cursor: " + wv_time(wv["cursor"]))
            wv_draw()

        wcanvas.bind("<Button-1>", wv_click)
        wcanvas.bind("<Configure>", wv_draw)
        wcanvas.bind("<MouseWheel>", lambda e: wcanvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        wcanvas.bind("<Control-MouseWheel>", lambda e: wv_zoom(1.5 if e.delta > 0 else 1 / 1.5,
                                                               wv["t0"] + max(e.x - NAME_W - VAL_W, 0) / wv["scale"]))
        wcanvas.bind("<Shift-MouseWheel>", lambda e: wv_hscroll("scroll", -1 if e.delta > 0 else 1, "units"))
        outtabs.select(con_f)

        def clear_all():
            """Empty every result tab of this side: console, log, report, coverage, pictures, waveform."""
            for t in (out, viewers["log"]["txt"], viewers["report"]["txt"]):
                t.delete("1.0", "end")
            for v in viewers.values():
                v["path"] = None
                v["var"].set("Nothing loaded yet. It fills in after a run.")
            cov_tree.delete(*cov_tree.get_children())
            cov_src.set("No coverage yet.")
            cov_state.update(dir=None, annot=None)
            for view in (sch_view, fsm_view):
                view["canvas"].delete("all")
                view.update(full=None, img=None, dot=None)
                view["var"].set("Nothing drawn yet.")
            wv.update(data=None, shown=[], t0=0.0, scale=1.0, cursor=None, path=None, sel=None)
            wlist.delete(0, "end")
            wv_file.set("No waveform loaded.")
            wv_cur.set("")
            wv_draw()
            outtabs.select(con_f)

        from types import SimpleNamespace
        return SimpleNamespace(nb=outtabs, con_f=con_f, out=out, viewers=viewers, show_text=show_text,
                               show_coverage=show_coverage, cov_tree=cov_tree, cov_src=cov_src,
                               show_image=show_image, sch_view=sch_view, fsm_view=fsm_view, wv=wv,
                               wv_load=wv_load, wv_file=wv_file, wv_draw=wv_draw, wv_zoom=wv_zoom,
                               wv_hscroll=wv_hscroll, wv_time=wv_time, wcanvas=wcanvas, clear_all=clear_all,
                               texts=[out, viewers["log"]["txt"], viewers["report"]["txt"]])

    P = make_results()      # result tabs of the Project side
    S = make_results()      # result tabs of the Single file side

    def show_panel(*_):
        on_single = tabs.select() == str(single)
        (P if on_single else S).nb.pack_forget()
        (S if on_single else P).nb.pack(fill="both", expand=True, padx=8, pady=(6, 0))
        clean_text.set("Clean file outputs" if on_single else "Clean project (make clean)")
    show_panel()

    ttk.Label(bottom, textvariable=cmd_var).pack(side="left")
    ttk.Button(bottom, text="Stop", command=lambda: stop()).pack(side="right")
    ttk.Button(bottom, textvariable=clean_text, command=lambda: clean_current()).pack(side="right", padx=4)
    ttk.Button(bottom, text="Clear (all result tabs)", command=lambda: current_panel().clear_all()).pack(side="right")
    ttk.Button(bottom, textvariable=theme_text, command=lambda: toggle_theme()).pack(side="right", padx=4)
    ttk.Label(bottom, textvariable=status_var).pack(side="right", padx=10)

    # ---- console theme (dark / light), remembered per user
    SETTINGS = Path(ENV["HOME"]) / ".oss_flow_settings.json"
    THEMES = {False: {"bg": "#ffffff", "fg": "#000000", "good": "#1a7f37", "bad": "#c62828", "warn": "#b26a00",
                      "cmd": "#555555", "sel": "#cce4ff"},
              True: {"bg": "#1e1e1e", "fg": "#d4d4d4", "good": "#6ad46a", "bad": "#ff6b6b", "warn": "#e5c07b",
                     "cmd": "#8b949e", "sel": "#264f78"}}

    def load_settings():
        try:
            import json
            return json.loads(SETTINGS.read_text())
        except Exception:
            return {}

    def apply_theme(dark):
        c = THEMES[dark]
        for pn in (P, S):
            for t in pn.texts:
                t.configure(background=c["bg"], foreground=c["fg"], insertbackground=c["fg"],
                            selectbackground=c["sel"])
                for tag in ("good", "bad", "warn", "cmd"):
                    t.tag_configure(tag, foreground=c[tag])
        state["dark"] = dark
        theme_text.set("Light console" if dark else "Dark console")

    def toggle_theme():
        apply_theme(not state.get("dark", False))
        try:
            import json
            SETTINGS.write_text(json.dumps({"dark": state["dark"]}))
        except OSError:
            pass

    def current_panel():
        return S if tabs.select() == str(single) else P

    def clean_current():
        if current_panel() is S:
            clean_single()
        else:
            clean_project()

    apply_theme(bool(load_settings().get("dark", False)))

    def clear(frame):
        for w in frame.winfo_children():
            w.destroy()

    def need_project():
        if not state["run"]:
            info("Choose a project first (Browse or New project).")
            return False
        return True

    def busy():
        if state["proc"]:
            info("A command is still running. Wait, or press Stop.")
            return True
        return False

    # ---- running make (or a single-file command) in a thread, output through the queue
    def run(args, after=None, shell=None, where=None, done=None, panel=None):
        """after(): only when the run passed; done(rc): always (e.g. load the log into the Log tab).
        panel: the result tabs to use (S for single files, P for projects)."""
        if shell is None and not need_project():
            return
        if busy():
            return
        pn = panel or (S if shell is not None else P)
        state["panel"] = pn
        out = pn.out
        pn.nb.select(pn.con_f)
        run_dir = where or state["run"]
        shown = shell or "make " + args
        cmd_var.set("Command used: {}   (in {})".format(shown, run_dir))
        status_var.set("Running ...")
        state["lines"] = []
        out.insert("end", "\n$ {}\n".format(shown), "cmd")
        out.see("end")

        def work():
            try:
                proc, job = start_make(run_dir, args, shell=shell)
                state["proc"], state["job"], state["stopped"] = proc, job, False
                for line in proc.stdout:
                    q.put(("line", line.rstrip("\r\n")))
                rc = proc.wait()
                job.close()
                q.put(("done", (rc, after, done)))
            except OSError as exc:
                q.put(("line", "Could not start the tools: {}".format(exc)))
                q.put(("done", (1, None, None)))
        threading.Thread(target=work, daemon=True).start()

    def pump():
        try:
            while True:
                kind, data = q.get_nowait()
                out = state["panel"].out
                if kind == "line":
                    state["lines"].append(data)
                    out.insert("end", data + "\n", line_tag(data))
                    out.see("end")
                else:
                    rc, after, done = data
                    state["proc"] = None
                    if state.get("stopped"):
                        status_var.set("Stopped by you")
                        out.insert("end", "== stopped by you (all tool processes ended) ==\n", "warn")
                        out.see("end")
                        continue
                    status_var.set("Finished: PASS (exit 0)" if rc == 0 else "Finished: FAIL (exit {})".format(rc))
                    out.insert("end", "== exit {} ==\n".format(rc), "good" if rc == 0 else "bad")
                    out.see("end")
                    for k, v in coverage_from(state["lines"]).items():
                        cov_vars[k].set("{:.1f}%".format(v))
                    if done:
                        try:
                            done(rc)
                        except Exception as exc:      # a viewer problem must never break the window
                            out.insert("end", "(could not update a result tab: {})\n".format(exc), "warn")
                    if after and rc == 0:
                        after()
        except queue.Empty:
            pass
        root.after(100, pump)

    def clean_project():
        if not need_project() or busy():
            return
        ok = messagebox.askyesno(
            "Clean project",
            "Run 'make clean' in\n{}?\n\nIt deletes only the files the flow created (build folder, logs, "
            "waveforms, reports, coverage, schematics).\nYour rtl/, tb/ and sva/ files are NOT touched.".format(state["run"]),
            parent=root, default="no")
        if ok:
            for v in cov_vars.values():
                v.set("-")
            names = ["code_coverage.html", "functional_coverage.html"]          # created by this launcher
            if state["flow"] == "design":
                names += [top_name() + sfx for sfx in ("_rtl.png", "_synth.png", "_fsm.png")]
            for n in names:
                f = state["run"] / n
                if f.exists():
                    f.unlink()
            run(("clean " + sim_arg()).strip(), done=lambda rc: P.clear_all(), panel=P)

    def sim_arg():
        """SIMULATOR=VERILATOR for 'Your Makefile' projects whose Makefile switches simulators."""
        return make_simulator(state["run"])[0] if state["flow"] == "make" else ""

    def single_outputs(f):
        """Files and folders that svrun / vrun / uvmrun created for this file (never the source itself)."""
        f = Path(f)
        d, n = f.parent, f.stem
        cands = [d / ("svrun_" + n), d / ("svrun_" + n + ".build.txt"), d / (n + ".log"), d / (n + ".out"),
                 d / (n + ".coverage.dat"), d / (n + "_cov_report.txt"), d / (n + "_cov_annot")]
        try:
            m = re.search(r'\$dumpfile\s*\(\s*"([^"]+)"', f.read_text(errors="replace"))
        except OSError:
            m = None
        if m and "/" not in m.group(1) and "\\" not in m.group(1):
            cands.append(d / m.group(1))                     # the waveform file named in the code
        return [p for p in cands if p.exists() and p.resolve() != f.resolve()]

    def clean_single():
        f = state.get("single")
        if not f or busy():
            S.clear_all()
            return
        items = single_outputs(f)
        if not items:
            S.clear_all()
            info("No generated files for {} (nothing to delete). All result tabs were cleared.".format(Path(f).name))
            return
        ok = messagebox.askyesno(
            "Clean file outputs",
            "Delete the files generated for {}?\n\n{}\n\nYour source file is NOT touched.".format(
                Path(f).name, "\n".join("  " + p.name + ("/" if p.is_dir() else "") for p in items)),
            parent=root, default="no")
        if ok:
            for p in items:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink()
            S.clear_all()
            S.out.insert("end", "Cleaned: {}\n".format(", ".join(p.name for p in items)), "cmd")

    def stop():
        if state["proc"] and state.get("job"):
            state["stopped"] = True
            state["job"].kill()          # ends make, compiler, simulation: the whole run
            status_var.set("Stopping ...")

    # ---- files and viewers
    def open_with(program, path):
        subprocess.Popen([str(program), str(path)], cwd=str(state["run"]), env=ENV)

    def open_default(path):
        path = Path(path)
        if path.exists():
            os.startfile(str(path))
        else:
            info("{} does not exist yet. Run the step that creates it first.".format(path.name))

    def edit(sub):
        if not need_project():
            return
        ext = [("Verilog / SystemVerilog", "*.v *.sv *.svh"), ("All files", "*.*")]
        # lab projects use other folder names (test/, env/, env_lib/): take the first that exists
        names = {"rtl": ["rtl"], "tb": ["tb", "test", "env", "env_lib", "testbench"]}.get(sub, [sub])
        start = next((state["project"] / n for n in names if (state["project"] / n).is_dir()), state["project"])
        f = filedialog.askopenfilename(parent=root, title="Open a file in gvim",
                                       initialdir=str(start), filetypes=ext)
        if f:
            open_with(GVIM, f)

    def new_file():
        if not need_project():
            return
        win, fr = dialog("New file")
        name_var = tk.StringVar()
        where_var = tk.StringVar(value="rtl")
        ext_var = tk.StringVar(value=".v" if state["flow"] == "design" else ".sv")
        ttk.Label(fr, text="Module name (the file gets the same name, e.g. alu -> alu.v):").grid(row=0, column=0, columnspan=2, sticky="w")
        entry = ttk.Entry(fr, textvariable=name_var, width=30)
        entry.grid(row=1, column=0, columnspan=2, sticky="we", pady=4)
        ttk.Radiobutton(fr, text="Design file (rtl/)", variable=where_var, value="rtl").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(fr, text="Testbench file (tb/)", variable=where_var, value="tb").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(fr, text="Verilog (.v)", variable=ext_var, value=".v").grid(row=3, column=0, sticky="w")
        ttk.Radiobutton(fr, text="SystemVerilog (.sv)", variable=ext_var, value=".sv").grid(row=3, column=1, sticky="w")
        rule = {"design": "Design flow: use .v for design and testbench files.",
                "sv": "SV flow: design files .v or .sv; testbench files .sv.",
                "uvm": "UVM flow: design files .v or .sv; testbench files .sv.",
                "basic": "Basic flow: design files .v or .sv; testbench files .sv.",
                "make": "Your Makefile: add the new file to the Makefile's file list too."}[state["flow"]]
        ttk.Label(fr, text=rule, foreground="#555555").grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))
        err = ttk.Label(fr, text="", foreground="#c62828")
        err.grid(row=5, column=0, columnspan=2, sticky="w")

        def create():
            name, where, ext = name_var.get().strip(), where_var.get(), ext_var.get()
            if not re.match(r"^[A-Za-z_]\w*$", name):
                err.config(text="Use letters, digits and _ only, starting with a letter.")
                return
            problem = file_rule_error(state["flow"], where, ext)
            if problem:
                err.config(text=problem)
                return
            f = state["project"] / where / (name + ext)
            if not f.exists():
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(module_skeleton(name, where == "tb", ext), newline="\n")
            win.destroy()
            open_with(GVIM, f)
        ttk.Button(fr, text="Create and open in gvim", command=create).grid(row=6, column=0, pady=(8, 0), sticky="w")
        ttk.Button(fr, text="Cancel", command=win.destroy).grid(row=6, column=1, pady=(8, 0), sticky="e")
        entry.focus_set()
        win.bind("<Return>", lambda e: create())

    def log_path():
        run_dir, flow, t = state["run"], state["flow"], test_var.get()
        if flow == "design":
            return run_dir / "sim_report.txt"
        if flow == "basic":
            return run_dir / "{}.log".format(t)
        if flow == "make":          # the newest log the Makefile wrote (test1.log, vcs.log, ...)
            return newest_file(run_dir, ["*.log"]) or run_dir / "(no .log file yet: run a test first)"
        return run_dir / "logs" / "{}.log".format(t)

    def open_log():
        if need_project():
            P.show_text("log", log_path())

    def waveform():
        if not need_project():
            return
        flow = state["flow"]
        if flow == "design":
            f, hint = state["run"] / "dump.vcd", "Click Simulate first."
        elif flow == "basic":
            f, hint = state["run"] / "waves.vcd", "Tick 'Save waveform' and click Run test first."
        elif flow == "make":        # the newest waveform the Makefile wrote
            f = newest_file(state["run"], ["*.vcd", "*.fst"]) or state["run"] / "(no .vcd or .fst file)"
            hint = "Run a test first (the Makefile decides the waveform file)."
        else:
            f = state["run"] / "waves_{}.{}".format(test_var.get(), fmt_var.get())
            hint = "Tick 'Save waveform', then Compile and Simulate."
        if not f.exists():
            info("{} not found. {}".format(f.name, hint))
            return
        P.wv_load(f)

    def terminal_here(where=None):
        """Opens the OSS Flow terminal (Verification_Terminal.cmd) in the given folder,
        else in the project's run folder, else in the home folder."""
        where = where or state["run"] or Path(ENV["HOME"])
        subprocess.Popen([str(TERMINAL_CMD)], cwd=str(where), creationflags=NEW_CONSOLE)

    def choose_single():
        start = Path(state["single"]).parent if state.get("single") else (state["project"] or Path(ENV["HOME"]))
        f = filedialog.askopenfilename(parent=root, title="Choose a .sv or .v file", initialdir=str(start),
                                       filetypes=[("SystemVerilog / Verilog", "*.sv *.v"), ("All files", "*.*")])
        if not f:
            return
        if " " in f:
            warn("The path has a space:\n{}\nMove the file to a folder without spaces.".format(f))
            return
        set_single(f)

    def set_single(f, kind=None):
        state["single"] = str(f)
        kind_var.set(kind or file_kind(f))
        file_var.set("{}   ({})".format(Path(f).name, Path(f).parent))

    def new_single():
        win, fr = dialog("New file")
        folder_var = tk.StringVar(value=str(Path(state["single"]).parent) if state.get("single")
                                  else str(Path(ENV["HOME"]) / "vlsi_work" / "single_files"))
        name_var = tk.StringVar(value="")
        nkind = tk.StringVar(value="SystemVerilog")
        starter = tk.BooleanVar(value=True)
        ttk.Label(fr, text="Save in folder (no spaces):").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Entry(fr, textvariable=folder_var, width=52).grid(row=1, column=0, columnspan=2, sticky="we")

        def pick_folder():
            d = filedialog.askdirectory(parent=win, title="Folder for the new file", initialdir=folder_var.get()
                                        if Path(folder_var.get()).exists() else str(Path(ENV["HOME"])))
            if d:
                folder_var.set(d)
        ttk.Button(fr, text="Browse...", command=pick_folder).grid(row=1, column=2, padx=4)
        ttk.Label(fr, text="File name (without extension):").grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        entry = ttk.Entry(fr, textvariable=name_var, width=30)
        entry.grid(row=3, column=0, columnspan=3, sticky="w")
        ttk.Label(fr, text="Type:").grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))
        for i, (label, k) in enumerate((("Verilog (.v)  - runs with vrun (Icarus Verilog)", "Verilog"),
                                        ("SystemVerilog (.sv)  - runs with svrun (Verilator)", "SystemVerilog"),
                                        ("UVM (.sv)  - runs with uvmrun (Verilator + UVM library)", "UVM"))):
            ttk.Radiobutton(fr, text=label, variable=nkind, value=k).grid(row=5 + i, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(fr, text="Start with a small working example (recommended)", variable=starter).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(8, 0))
        err = ttk.Label(fr, text="", foreground="#c62828")
        err.grid(row=9, column=0, columnspan=3, sticky="w")

        def create():
            name = name_var.get().strip()
            for ext in (".sv", ".v"):
                if name.lower().endswith(ext):
                    name = name[: -len(ext)]
            folder = Path(folder_var.get().strip())
            if not re.match(r"^[A-Za-z_]\w*$", name):
                err.config(text="File name: letters, digits and _ only, starting with a letter.")
                return
            if " " in str(folder):
                err.config(text="The folder path has a space. Choose a folder without spaces.")
                return
            k = nkind.get()
            f = folder / (name + (".v" if k == "Verilog" else ".sv"))
            if f.exists():
                if not messagebox.askyesno("New file", "{} already exists.\nOpen the existing file instead?".format(f),
                                           parent=win):
                    return
            else:
                folder.mkdir(parents=True, exist_ok=True)
                body = single_starter(name, k) if starter.get() else (
                    "module {} ;\n  initial begin\n\n  end\nendmodule\n".format(name))
                f.write_text(body, newline="\n")
            win.destroy()
            set_single(f, k)
            tabs.select(single)
            subprocess.Popen([str(GVIM), str(f)], cwd=str(f.parent), env=ENV)
            S.out.insert("end", "\nCreated {} ({}). Write your code in gvim, save with Ctrl+S, then Compile and "
                              "Simulate.\n".format(f, k), "cmd")
        ttk.Button(fr, text="Create and open in gvim", command=create).grid(row=10, column=0, pady=(8, 0), sticky="w")
        ttk.Button(fr, text="Cancel", command=win.destroy).grid(row=10, column=2, pady=(8, 0), sticky="e")
        entry.focus_set()
        win.bind("<Return>", lambda e: create())

    def single_edit():
        if not state.get("single"):
            info("Click 'Choose file...' first.")
            return
        subprocess.Popen([str(GVIM), state["single"]], cwd=str(Path(state["single"]).parent), env=ENV)

    def single_run(mode):
        f = state.get("single")
        if not f:
            info("Click 'Choose file...' first (a .sv or .v file).")
            return
        lint = mode == "lint"
        kind = kind_var.get()
        where, cmd = single_file_command(f, lint=lint, extra="" if lint else args_var.get(),
                                         mode="" if lint else mode, kind=kind)
        if kind == "UVM" and mode in ("", "compile"):
            S.out.insert("end", "\nUVM file: the first compile takes several minutes. Simulate reuses it.\n", "warn")
        name = Path(f).stem

        def loaded(rc):
            if mode in ("", "sim"):
                S.show_text("log", Path(f).parent / (name + ".log"), select=False)
                if "--cov" in args_var.get():
                    S.show_coverage(Path(f).parent / (name + "_cov_report.txt"), select=False)
        run("", shell=cmd, where=where, done=loaded, panel=S)

    def single_waveform():
        f = state.get("single")
        folder = Path(f).parent if f else Path(ENV["HOME"])
        vcds = sorted(folder.glob("*.vcd"), key=lambda p: p.stat().st_mtime, reverse=True)
        if vcds:
            S.wv_load(vcds[0])
        else:
            info("No .vcd file in {}.\nYour code needs $dumpfile(\"dump.vcd\"); $dumpvars; and for .sv files put "
                 "--waves in Arguments, then Compile and Simulate. Or use 'Open VCD...' in the Waveform tab."
                 .format(folder))

    def single_coverage():
        f = state.get("single")
        if not f:
            info("Click 'Choose file...' first.")
            return
        S.show_coverage(Path(f).parent / (Path(f).stem + "_cov_report.txt"))

    def run_args():
        a = "TEST={} SEED={}".format(test_var.get(), seed_var.get().strip() or "1")
        if state["flow"] == "uvm":
            a += " VERBOSITY={}".format(verb_var.get())
        if waves_var.get():
            a += " WAVES=1 WAVE_FMT={}".format(fmt_var.get())
        return a

    def top_name():
        m = re.search(r"^TOP\s*\?=\s*(\S+)", makefile_text(state["run"]), re.M)
        return m.group(1) if m else "top"

    def button(row, text, cmd):
        ttk.Button(row, text=text, command=cmd).pack(side="left", padx=2)

    # ---- build the button rows for the detected flow
    def build_rows():
        for f in (write_row, opts_row, btn_row, cov_row, res_btn_row):
            clear(f)
        flow, rd = state["flow"], state["run"]
        button(write_row, "New file", new_file)
        button(write_row, "Edit RTL", lambda: edit("rtl"))
        button(write_row, "Edit testbench", lambda: edit("tb"))
        if flow == "design":
            button(write_row, "Lint", lambda: run("lint", done=lambda rc: P.show_text("report", rd / "lint_report.txt", select=False)))
        elif flow != "make" or has_target(rd, "lint"):
            button(write_row, "Lint", lambda: run(("lint " + sim_arg()).strip()))
        if flow == "uvm":
            button(write_row, "Lint testbench", lambda: run("lint_tb"))
        opts_row.pack(fill="x")
        btn_row.pack(fill="x", pady=4)
        res_btn_row.pack(fill="x", pady=4)
        if flow == "make":
            build_make_rows(rd)
            return
        if flow == "design":
            def sch(which):
                P.sch_view["which"].set("RTL schematic" if which == "rtl" else "Gate schematic")
                run("schematic", lambda: P.show_image(P.sch_view, rd / (top_name() + ("_rtl.dot" if which == "rtl" else "_synth.dot"))))
            button(btn_row, "Simulate", lambda: run("sim", done=lambda rc: P.show_text("log", rd / "sim_report.txt", select=False)))
            button(btn_row, "Waveform", waveform)
            button(btn_row, "Synthesize", lambda: run("synth", lambda: P.show_text("report", rd / "synth_stat.txt")))
            button(btn_row, "Schematic", lambda: sch("rtl"))
            button(btn_row, "Gate schematic", lambda: sch("synth"))
            button(btn_row, "FSM diagram", lambda: run("fsm", lambda: P.show_image(P.fsm_view, rd / (top_name() + "_fsm.dot"))))
            button(res_btn_row, "Full report", lambda: run("report", done=lambda rc: P.show_text("report", rd / "flow_report.txt")))
            button(res_btn_row, "Open log", open_log)
            ttk.Label(res_btn_row, text="(results open in the tabs below)", foreground="#555555").pack(side="left", padx=8)
            return
        tests = tests_from(rd)
        test_var.set(tests[0] if tests else "")       # never keep the previous project's test name
        ttk.Label(opts_row, text="Test").pack(side="left")
        ttk.Combobox(opts_row, textvariable=test_var, values=tests, width=22).pack(side="left", padx=4)
        if flow != "basic":
            ttk.Label(opts_row, text="Seed").pack(side="left")
            ttk.Entry(opts_row, textvariable=seed_var, width=7).pack(side="left", padx=4)
        if flow == "uvm":
            ttk.Label(opts_row, text="Verbosity").pack(side="left")
            ttk.Combobox(opts_row, textvariable=verb_var, width=12,
                         values=["UVM_LOW", "UVM_MEDIUM", "UVM_HIGH"]).pack(side="left", padx=4)
        ttk.Checkbutton(opts_row, text="Save waveform", variable=waves_var).pack(side="left", padx=8)
        show_log = lambda rc: P.show_text("log", log_path(), select=False)
        if flow != "basic":
            ttk.Radiobutton(opts_row, text="VCD", variable=fmt_var, value="vcd").pack(side="left")
            ttk.Radiobutton(opts_row, text="FST", variable=fmt_var, value="fst").pack(side="left")
            if has_target(rd, "sim"):
                button(btn_row, "Compile", lambda: run("build WAVE_FMT={}".format(fmt_var.get())))
                button(btn_row, "Simulate", lambda: run("sim " + run_args(), done=show_log))
                ttk.Label(opts_row, text="(after changing VCD/FST, click Compile again)",
                          foreground="#555555").pack(side="left", padx=6)
            else:
                button(btn_row, "Run test", lambda: run("run " + run_args(), done=show_log))
        else:
            button(btn_row, "Run test", lambda: run(test_var.get() + (" WAVES=1" if waves_var.get() else ""), done=show_log))
        button(btn_row, "Regression", lambda: run("regress"))
        button(btn_row, "Waveform", waveform)
        if has_target(rd, "synth"):
            stat = rd / ("synth_stat.txt" if flow == "basic" else "synth.log")
            button(btn_row, "Synthesize", lambda: run("synth", lambda: P.show_text("report", stat)))
        cov_target = "covtxt" if flow == "basic" else "cov"
        cov_file = rd / ("cov_summary.txt" if flow == "basic" else "cov_report.txt")
        button(res_btn_row, "Coverage", lambda: run(cov_target, lambda: P.show_coverage(cov_file)))
        button(res_btn_row, "Open log", open_log)
        hint = "(results open in the tabs below"
        hint += "; first UVM compile: several minutes, about 3.5 GB RAM)" if flow == "uvm" else ")"
        ttk.Label(res_btn_row, text=hint, foreground="#555555").pack(side="left", padx=8)

    # ---- 'Your Makefile' projects: tests, regressions and other targets are read from the Makefile
    def build_make_rows(rd):
        targets = make_targets(rd)
        simarg, simdef = make_simulator(rd)
        tests = [t for t in targets if TEST_TARGET_RE.match(t)]
        regs = [t for t in targets if t.lower().startswith("regress")]
        others = [t for t in targets if t not in tests and t not in regs]
        test_var.set(tests[0] if tests else "")
        reg_var.set(regs[-1] if regs else "")
        target_var.set(next((t for t in others if t.lower().startswith("report")), others[0] if others else ""))
        seed_var.set("")

        def mk(*parts):
            return " ".join(p for p in parts + (simarg,) if p)

        def cov_report():
            return newest_file(rd, ["*.txt"], must_contain="Coverage Summary")

        def show_results(rc, log=True):
            if log:
                P.show_text("log", log_path(), select=False)
            cov = cov_report()
            if cov:
                P.show_coverage(cov, select=False)

        def run_test():
            t = test_var.get().strip()
            if not t:
                info("No test target (TC1, TC2, ...) was found in the Makefile.")
                return
            run(mk(t, make_seed_arg(rd, t, seed_var.get())), done=show_results)

        def run_regression():
            t = reg_var.get().strip()
            if not t:
                info("No regression target (regress...) was found in the Makefile.")
                return
            run(mk(t), done=show_results)

        def run_target():
            t = target_var.get().strip()
            if t:
                run(mk(t), done=lambda rc: show_results(rc, log=False))

        def coverage():
            cov = cov_report()
            if cov:
                P.show_coverage(cov)
            else:
                info("No coverage report yet in\n{}\nRun a test or a regression first.".format(rd))

        ttk.Label(opts_row, text="Test").pack(side="left")
        ttk.Combobox(opts_row, textvariable=test_var, values=tests, width=14).pack(side="left", padx=4)
        ttk.Label(opts_row, text="Seed").pack(side="left")
        ttk.Entry(opts_row, textvariable=seed_var, width=11).pack(side="left", padx=4)
        ttk.Label(opts_row, text="(empty: the Makefile's seed)", foreground="#555555").pack(side="left", padx=(0, 10))
        button(opts_row, "Run test", run_test)
        ttk.Label(btn_row, text="Regression").pack(side="left")
        ttk.Combobox(btn_row, textvariable=reg_var, values=regs, width=14).pack(side="left", padx=4)
        button(btn_row, "Run regression", run_regression)
        ttk.Label(btn_row, text="Other target").pack(side="left", padx=(12, 0))
        ttk.Combobox(btn_row, textvariable=target_var, values=others, width=14).pack(side="left", padx=4)
        button(btn_row, "Run target", run_target)
        button(btn_row, "Waveform", waveform)
        button(res_btn_row, "Coverage", coverage)
        button(res_btn_row, "Open log", open_log)
        if simarg:
            note = "Every make command gets {} (the Makefile's own default is {}).".format(simarg, simdef)
        elif simdef:
            note = "Note: this Makefile has no VERILATOR part; SIMULATOR={} needs tools that are not installed.".format(simdef)
        else:
            note = "Targets found in the Makefile: {}".format(len(targets))
        ttk.Label(res_btn_row, text=note, foreground="#555555").pack(side="left", padx=8)

    def set_project(path):
        flow, run_dir = detect(path)
        if not flow:
            warn("No Makefile found in\n{}\n(looked in sim/, simdir/ and the folder itself)".format(path))
            return
        # a chosen sim/ or simdir/ folder: the project is the folder above it
        path = run_dir.parent if Path(run_dir) == Path(path) else Path(path)
        state.update(project=Path(path), flow=flow, run=run_dir)
        proj_var.set(str(path))
        flow_var.set("Flow: {}   |   run folder: {}".format(FLOW_NAMES[flow], run_dir))
        for v in cov_vars.values():
            v.set("-")
        build_rows()
        tabs.select(ptab)
        fit_top()          # the project's buttons were just added: give the Project tab its full height

    def browse():
        d = filedialog.askdirectory(parent=root, title="Choose the project folder, or its sim/ folder (the one with the Makefile)")
        if d:
            set_project(d)

    def new_project():
        examples = sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir())
        win, fr = dialog("New project")
        ex_var = tk.StringVar(value=examples[0] if examples else "")
        name_var = tk.StringVar(value="my_" + ex_var.get())
        ttk.Label(fr, text="Start from this example:").grid(row=0, column=0, sticky="w")
        for i, ex in enumerate(examples, start=1):
            ttk.Radiobutton(fr, text="{}  -  {}".format(ex, EXAMPLE_INFO.get(ex, "")), variable=ex_var, value=ex,
                            command=lambda e=ex: name_var.set("my_" + e)).grid(row=i, column=0, columnspan=2, sticky="w")
        r = len(examples) + 1
        ttk.Label(fr, text="Project name (no spaces):").grid(row=r, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(fr, textvariable=name_var, width=30).grid(row=r + 1, column=0, columnspan=2, sticky="we")
        parent = Path(ENV["HOME"]) / "vlsi_work"
        ttk.Label(fr, text="It will be created in {}".format(parent)).grid(row=r + 2, column=0, columnspan=2, sticky="w")
        err = ttk.Label(fr, text="", foreground="#c62828")
        err.grid(row=r + 3, column=0, columnspan=2, sticky="w")

        def create():
            name = name_var.get().strip()
            if not re.match(r"^[A-Za-z_][\w-]*$", name):
                err.config(text="Use letters, digits, _ or - only (no spaces).")
                return
            target = parent / name
            if target.exists():
                err.config(text="{} already exists. Choose another name.".format(target.name))
                return
            parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(EXAMPLES / ex_var.get(), target)
            win.destroy()
            set_project(target)
        ttk.Button(fr, text="Create project", command=create).grid(row=r + 4, column=0, pady=(8, 0), sticky="w")
        ttk.Button(fr, text="Cancel", command=win.destroy).grid(row=r + 4, column=1, pady=(8, 0), sticky="e")
        win.bind("<Return>", lambda e: create())

    if len(sys.argv) > 1 and Path(sys.argv[1]).is_dir():
        set_project(sys.argv[1])
    if os.environ.get("OSSFLOW_GUI_SMOKE"):
        # maintainer check: build the window, open a project and both tabs, then close
        root.update()
        print("  Screen scaling: {:.0f} % (UI {:.2f}) | Tk scaling {:.2f} | window {} | Graphviz dpi {}".format(
            UI * 100, UI, float(root.tk.call("tk", "scaling")), root.geometry(), DOT_DPI))
        for d in os.environ["OSSFLOW_GUI_SMOKE"].split(";"):
            if d:
                set_project(d)
                root.update()
                need, got = ptab.winfo_reqheight(), ptab.winfo_height()
                print("  Project tab height: needs {} px, gets {} px -> {}".format(
                    need, got, "OK, all buttons visible" if got >= need else "CUT OFF (bug)"))
                print("GUI OK with project:", d, "| flow:", state["flow"],
                      "| buttons:", ", ".join(w.cget("text") for w in btn_row.winfo_children() if hasattr(w, "invoke")),
                      "|", ", ".join(w.cget("text") for w in res_btn_row.winfo_children() if hasattr(w, "invoke")))
                rd = state["run"]
                if state["flow"] == "design":
                    P.show_text("log", rd / "sim_report.txt")
                    P.show_text("report", rd / "flow_report.txt")
                    root.update()
                    print("  Log tab:", P.viewers["log"]["var"].get(), "| lines:", int(P.viewers["log"]["txt"].index("end").split(".")[0]) - 1)
                    print("  Report tab:", P.viewers["report"]["var"].get())
                    P.show_image(P.sch_view, rd / (top_name() + "_rtl.dot"))
                    root.update()
                    print("  Schematic tab:", P.sch_view["var"].get(), "| zoom", P.sch_view["zoom"].get())
                    P.show_image(P.fsm_view, rd / (top_name() + "_fsm.dot"))
                    root.update()
                    print("  FSM tab:", P.fsm_view["var"].get())
                    P.wv_load(rd / "dump.vcd")
                elif state["flow"] in ("sv", "uvm"):
                    P.show_coverage(rd / "cov_report.txt")
                    root.update()
                    print("  Coverage tab:", P.cov_src.get(), "| rows:", len(P.cov_tree.get_children()),
                          "top-level, e.g.", [P.cov_tree.item(i, "text") + " " + str(P.cov_tree.item(i, "values")[0])
                                              for i in P.cov_tree.get_children()][:4])
                    test_var.set("random")
                    P.show_text("log", log_path())
                    root.update()
                    print("  Log tab:", P.viewers["log"]["var"].get())
                    fmt_var.set("vcd")
                    waveform()
                elif state["flow"] == "make":
                    combos = [w for w in list(opts_row.winfo_children()) + list(btn_row.winfo_children())
                              if isinstance(w, ttk.Combobox)]
                    print("  Makefile dropdowns: test {} | regression {} | other {}".format(
                        *[list(c.cget("values")) for c in combos]))
                    print("  Preselected: test '{}' | regression '{}' | other '{}' | seed '{}'".format(
                        test_var.get(), reg_var.get(), target_var.get(), seed_var.get()))
                    print("  Note:", [w.cget("text") for w in res_btn_row.winfo_children() if isinstance(w, ttk.Label)])
                    if os.environ.get("OSSFLOW_GUI_SMOKE_MAKE_RUN"):
                        import time
                        if not state.get("pump_started"):
                            state["pump_started"] = True
                            root.after(100, pump)
                        seed_var.set("77")
                        run_btn = [w for w in opts_row.winfo_children() if hasattr(w, "invoke") and w.cget("text") == "Run test"][0]
                        n_exit = P.out.get("1.0", "end").count("== exit")
                        run_btn.invoke()
                        t_end = time.time() + 900
                        while P.out.get("1.0", "end").count("== exit") == n_exit and time.time() < t_end:
                            root.update()
                            time.sleep(0.05)
                        root.update()
                        print("  Run test pressed ->", cmd_var.get().split("   (in")[0], "|", status_var.get())
                        print("    Log tab:", P.viewers["log"]["var"].get().split("   (")[0],
                              "| Coverage tab:", P.cov_src.get().split("   (")[0], "| coverage rows:", len(P.cov_tree.get_children()))
                        waveform()
                        print("    Waveform:", P.wv_file.get())
                if P.wv["data"]:
                    root.update()
                    n0 = len(P.wcanvas.find_all())
                    P.wv_zoom(4.0)
                    P.wv_hscroll("scroll", 3, "pages")
                    P.wv["cursor"] = P.wv["t0"] + 10 / P.wv["scale"]
                    P.wv_draw()
                    root.update()
                    print("  Waveform tab:", P.wv_file.get(), "| shown:", len(P.wv["shown"]), "| items fit/zoomed:", n0,
                          len(P.wcanvas.find_all()), "| t0 after scroll:", P.wv_time(P.wv["t0"]))
        tabs.select(single)
        root.update()
        print("GUI OK: single-file tab buttons:", ", ".join(w.cget("text") for w in srow2.winfo_children()))
        need, got = single.winfo_reqheight(), single.winfo_height()
        print("  Single file tab height: needs {} px, gets {} px -> {} | result tabs height: {} px".format(
            need, got, "OK" if got >= need else "CUT OFF (bug)", S.nb.winfo_height()))
        tabs.select(ptab)
        root.update()
        need, got = ptab.winfo_reqheight(), ptab.winfo_height()
        print("  Back to Project tab: needs {} px, gets {} px -> {}".format(
            need, got, "OK" if got >= need else "CUT OFF (bug)"))
        tabs.select(single)
        root.update()
        sdir = os.environ.get("OSSFLOW_GUI_SMOKE_SINGLE")
        if sdir:
            import time
            if not state.get("pump_started"):
                state["pump_started"] = True
                root.after(100, pump)

            def press(mode):
                n_exit = S.out.get("1.0", "end").count("== exit")
                single_run(mode)
                t_end = time.time() + 900
                while S.out.get("1.0", "end").count("== exit") == n_exit and time.time() < t_end:
                    root.update()
                    time.sleep(0.05)
                root.update()
            kinds = ["Verilog", "SystemVerilog"] + (["UVM"] if os.environ.get("OSSFLOW_GUI_SMOKE_UVM") else [])
            for k in kinds:
                name = "starter_" + k.lower()
                f = Path(sdir) / (name + (".v" if k == "Verilog" else ".sv"))
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(single_starter(name, k), newline="\n")
                set_single(f)
                S.out.delete("1.0", "end")
                press("compile")
                press("sim")
                text = S.out.get("1.0", "end").splitlines()
                shown = [l for l in text if l.startswith(("time=", "addr =", "UVM_INFO")) and "RELNOTES" not in l]
                print("  Single file {} -> type {} -> command '{}': console shows {} output lines, e.g. {}".format(
                    f.name, kind_var.get(), cmd_var.get().split("   (in")[0].replace("Command used: ", ""),
                    len(shown), shown[:2]))
                print("    Log tab:", S.viewers["log"]["var"].get().split("   (")[0],
                      "| last console line:", [l for l in text if l.strip()][-1])
            # Single file and Project must not share results
            ptext = P.out.get("1.0", "end")
            print("  Separation: project console has single-file output? {} | single waveform from project? {}".format(
                "YES (bug)" if "starter_" in ptext else "no, OK",
                "YES (bug)" if S.wv["path"] and state["run"] and str(state["run"]) in str(S.wv["path"]) else "no, OK"))
            # Clean file outputs (answer Yes to the question automatically)
            messagebox.askyesno = lambda *a, **k: True
            last = Path(state["single"])
            before = [p.name for p in single_outputs(last)]
            clean_single()
            root.update()
            print("  Clean file outputs for {}: removed {} | left {} | source kept: {} | console lines {} | log tab: {}".format(
                last.name, before, [p.name for p in single_outputs(last)], last.exists(),
                int(S.out.index("end").split(".")[0]) - 2, S.viewers["log"]["var"].get()[:30]))
        S.wv_load(next(iter(Path(sdir).glob("*.vcd")), None)) if sdir and list(Path(sdir).glob("*.vcd")) else None
        S.out.insert("end", "some text\n")
        S.clear_all()
        root.update()
        print("  Clear: console empty: {} | waveform empty: {} | coverage rows: {} | project tabs untouched: {}".format(
            S.out.get("1.0", "end").strip() == "", S.wv["data"] is None, len(S.cov_tree.get_children()),
            P.wv["data"] is not None or not os.environ.get("OSSFLOW_GUI_SMOKE").strip(";")))
        was = state.get("dark", False)
        toggle_theme()
        bg1 = S.out.cget("background")
        toggle_theme()
        print("  Theme switch: {} -> {} -> {} | button now: {}".format(
            "dark" if was else "light", bg1, S.out.cget("background"), theme_text.get()))
        root.destroy()
        return
    root.after(100, pump)
    root.mainloop()


# ------------------------------------------------------------------ self-test (no window)
def selftest(workdir, with_uvm):
    """Runs the launcher's own functions on copies of the examples. Prints PASS/FAIL per check."""
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=False)
    results = []

    def check(name, ok, info=""):
        results.append(ok)
        print("{:<50} {}  {}".format(name, "PASS" if ok else "FAIL", info), flush=True)

    names = ["design_seq_det", "sv_project", "counter"] + (["uvm_project"] if with_uvm else [])
    for ex in names:
        shutil.copytree(EXAMPLES / ex, work / ex)
    lines = []
    collect = lines.append
    flow, rd = detect(work / "design_seq_det")
    check("detect design_seq_det", flow == "design", flow)
    for t in ("sim", "lint", "synth", "schematic", "fsm", "report"):
        check("design: make " + t, run_make(rd, t, collect) == 0)
    check("design: dump.vcd for Waveform", (rd / "dump.vcd").exists())
    check("design: rtl, gate and FSM svg created",
          all((rd / n).exists() for n in ("seq_det_rtl.svg", "seq_det_synth.svg", "seq_det_fsm.svg")))
    flow, rd = detect(work / "sv_project")
    check("detect sv_project", flow == "sv", flow)
    tests = tests_from(rd)
    check("sv: tests read from Makefile", tests == ["smoke", "random"], " ".join(tests))
    lines.clear()
    check("sv: make sim before Compile says so", run_make(rd, "sim TEST=smoke", collect) != 0
          and any("Not compiled yet" in l for l in lines))
    lines.clear()
    check("sv: Compile (make build) only", run_make(rd, "build WAVE_FMT=vcd", collect) == 0
          and not any("== smoke" in l for l in lines))
    lines.clear()
    check("sv: Simulate (make sim) without compiling", run_make(rd, "sim TEST=smoke SEED=1", collect) == 0
          and any("== smoke: PASS" in l for l in lines) and not any("verilator --binary" in l for l in lines))
    check("sv: make run TEST=random SEED=3 WAVES=1 WAVE_FMT=fst",
          run_make(rd, "run TEST=random SEED=3 WAVES=1 WAVE_FMT=fst", collect) == 0)
    check("sv: waves_random.fst for Waveform", (rd / "waves_random.fst").exists())
    check("sv: make regress", run_make(rd, "regress", collect) == 0)
    lines.clear()
    check("sv: make cov", run_make(rd, "cov", collect) == 0)
    cov = coverage_from(lines)
    check("sv: coverage numbers parsed", "line" in cov and "covergroup" in cov, str(cov))
    check("sv: make covhtml + index.html", run_make(rd, "covhtml", collect) == 0 and (rd / "cov_html" / "index.html").exists())
    check("sv: has synth target + make synth", has_target(rd, "synth") and run_make(rd, "synth", collect) == 0)
    check("sv: log for Open log", (rd / "logs" / "random.log").exists())
    code, func = write_coverage_html(rd)
    ctext = code.read_text(encoding="utf-8") if code else ""
    ftext = func.read_text(encoding="utf-8") if func else ""
    check("sv: code coverage report written", "Per module" in ctext and "toggle" in ctext and "cov_html/index.html" in ctext)
    check("sv: functional report lists bins", "alu_cg.cp_op.add" in ftext and "Covergroups" in ftext)
    check("sv: functional report lists cover properties", "c_add_carry" in ftext)
    check("file rule: design + .sv refused", file_rule_error("design", "rtl", ".sv") != "")
    check("file rule: sv tb + .v refused, sv rtl + .v allowed",
          file_rule_error("sv", "tb", ".v") != "" and file_rule_error("sv", "rtl", ".v") == "")
    check("skeleton .sv uses logic, .v uses wire", "logic" in module_skeleton("a", False, ".sv") and "wire" in module_skeleton("a", False, ".v"))
    flow, rd = detect(work / "counter")
    check("detect counter (basic template)", flow == "basic", flow)
    check("basic: tests read from Makefile", tests_from(rd) == ["TC1", "TC2"], " ".join(tests_from(rd)))
    check("basic: make TC1 WAVES=1", run_make(rd, "TC1 WAVES=1", collect) == 0)
    check("basic: waves.vcd for Waveform", (rd / "waves.vcd").exists())
    check("basic: TC1.log for Open log", (rd / "TC1.log").exists())
    check("basic: make regress", run_make(rd, "regress", collect) == 0)
    lines.clear()
    check("basic: make covtxt", run_make(rd, "covtxt", collect) == 0)
    check("basic: coverage numbers parsed", "line" in coverage_from(lines))
    lines.clear()
    check("basic: has synth target + make synth", has_target(rd, "synth") and run_make(rd, "synth", collect) == 0)
    check("basic: synth statistics printed", any("cells" in l for l in lines))
    for ex in ("design_seq_det", "sv_project", "counter"):
        flow, rd = detect(work / ex)
        src = sorted(str(p.relative_to(work / ex)) for p in (work / ex).rglob("*")
                     if p.is_file() and p.parts[len((work / ex).parts)] in ("rtl", "tb", "sva"))
        rc = run_make(rd, "clean", collect)
        left = sorted(str(p.relative_to(work / ex)) for p in (work / ex).rglob("*")
                      if p.is_file() and p.parts[len((work / ex).parts)] in ("rtl", "tb", "sva"))
        for n in ("code_coverage.html", "functional_coverage.html"):
            if (rd / n).exists():
                (rd / n).unlink()
        outputs = [p.name for p in rd.iterdir() if p.name != "Makefile"]
        check("clean {}: exit 0, sources kept".format(ex), rc == 0 and src == left and len(src) > 0, "{} source files".format(len(src)))
        check("clean {}: outputs removed".format(ex), not outputs, " ".join(outputs))
    # Stop: a long make run must end completely, including the program make started
    import time
    stop_dir = work / "stop_test" / "sim"
    stop_dir.mkdir(parents=True)
    (stop_dir / "Makefile").write_text("long:\n\t@echo started; sleep 300; echo should-not-print\n", newline="\n")

    def sleeps():
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq sleep.exe", "/NH"], capture_output=True, text=True)
        return r.stdout.lower().count("sleep.exe")
    base = sleeps()
    proc, job = start_make(stop_dir, "long")
    time.sleep(4)
    running = sleeps() - base
    job.kill()
    time.sleep(2)
    check("stop: run was going before Stop", running >= 1, "{} sleep.exe".format(running))
    check("stop: make and its child ended", proc.poll() is not None and sleeps() - base == 0,
          "left: {}".format(sleeps() - base))
    job.close()
    # Single file: svrun / vrun, the same commands the 'Single file' buttons use
    sf = work / "single"
    sf.mkdir()
    (sf / "const_top.sv").write_text(
        "class pkt; rand int a; real b; constraint c1 {a inside {[555:655]};}\n"
        "  function void post_randomize; b = a/10.0; endfunction endclass\n"
        "module const_top; initial begin static pkt p = new();\n"
        "  repeat (5) begin void'(p.randomize()); $display(\"value %0.1f\", p.b); end end endmodule\n", newline="\n")
    (sf / "and2.v").write_text(
        "module and2(input a, b, output y); assign y = a & b; endmodule\n"
        "module and2_tb; reg a, b; wire y; and2 d(a, b, y);\n"
        "  initial begin {a,b} = 2'b11; #1 $display(\"y=%b\", y); end endmodule\n", newline="\n")
    lines.clear()
    where, cmd = single_file_command(sf / "const_top.sv")
    rc = run_make_shell(where, cmd, collect)
    vals = [float(l.split()[1]) for l in lines if l.startswith("value ")]
    check("single file: svrun prints constrained values", rc == 0 and len(vals) == 5 and all(55.5 <= v <= 65.5 for v in vals),
          " ".join(str(v) for v in vals))
    lines.clear()
    where, cmd = single_file_command(sf / "and2.v")
    check("single file: vrun runs Verilog", run_make_shell(where, cmd, collect) == 0 and "y=1" in lines)
    lines.clear()
    where, cmd = single_file_command(sf / "const_top.sv", mode="compile")
    rc = run_make_shell(where, cmd, collect)
    check("single file: Compile only (no simulation output)", rc == 0 and any("COMPILE PASSED" in l for l in lines)
          and not any(l.startswith("value ") for l in lines))
    lines.clear()
    where, cmd = single_file_command(sf / "const_top.sv", mode="sim")
    rc = run_make_shell(where, cmd, collect)
    check("single file: Simulate only (no compile)", rc == 0 and not any("compiling" in l for l in lines)
          and len([l for l in lines if l.startswith("value ")]) == 5)
    lines.clear()
    shutil.copy(sf / "and2.v", sf / "fresh2.v")
    where, cmd = single_file_command(sf / "fresh2.v", mode="sim")
    rc = run_make_shell(where, cmd, collect)
    check("single file: Simulate before Compile says so", rc != 0 and any("Not compiled yet" in l for l in lines))
    lines.clear()
    where, cmd = single_file_command(sf / "and2.v", lint=True)
    rc = run_make_shell(where, cmd, collect)
    check("single file: lint reports -Wall findings", rc != 0 and any("DECLFILENAME" in l for l in lines))
    sk = module_skeleton("my_tb", True, ".v")
    check("new file: testbench skeleton has PASS line + dump", "PASS: all checks passed" in sk and "$dumpfile" in sk)
    if with_uvm:
        flow, rd = detect(work / "uvm_project")
        check("detect uvm_project", flow == "uvm", flow)
        check("uvm: make run (VERBOSITY, WAVES)", run_make(
            rd, "run TEST=alu_smoke_test SEED=1 VERBOSITY=UVM_LOW WAVES=1 WAVE_FMT=vcd", collect) == 0)
        check("uvm: waveform file", (rd / "waves_alu_smoke_test.vcd").exists())
        lines.clear()
        check("uvm: make cov", run_make(rd, "cov", collect) == 0)
        check("uvm: coverage numbers parsed", "covergroup" in coverage_from(lines))
    print("SELFTEST {}: {} of {} checks passed".format(
        "PASSED" if all(results) else "FAILED", sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--selftest":
        sys.exit(selftest(sys.argv[2], "--uvm" in sys.argv))
    gui()
