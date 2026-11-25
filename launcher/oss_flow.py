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
              "uvm": "UVM verification", "basic": "Basic SystemVerilog (TC1, TC2 tests)"}


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
    """Return (flow, run_dir) for a project folder: design, sv, uvm or basic."""
    p = Path(project)
    if (p / "simdir" / "Makefile").exists():
        return "design", p / "simdir"
    mk = p / "sim" / "Makefile"
    if mk.exists():
        text = mk.read_text(errors="replace")
        if "UVM_HOME" in text:
            return "uvm", p / "sim"
        if re.search(r"^TC%:", text, re.M):
            return "basic", p / "sim"
        return "sv", p / "sim"
    return None, None


def makefile_text(run_dir):
    mk = Path(run_dir) / "Makefile"
    return mk.read_text(errors="replace") if mk.exists() else ""


def tests_from(run_dir):
    m = TESTS_RE.search(makefile_text(run_dir))
    return m.group(1).split() if m else []


def has_target(run_dir, target):
    return re.search(r"^{}\s*:".format(re.escape(target)), makefile_text(run_dir), re.M) is not None


def make_command(run_dir, args):
    """bash --login -c 'cd <dir> && make <args>' with the bundle's tools."""
    script = "cd {} && make --no-print-directory {}".format(
        shq(str(run_dir).replace("\\", "/")), args)
    return [str(BASH), "--login", "-c", script]


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


def start_make(run_dir, args):
    """Start 'make <args>' in its own job; returns (process, job)."""
    job = Job()
    proc = job.start(make_command(run_dir, args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     env=ENV, creationflags=NO_WINDOW, text=True, encoding="utf-8", errors="replace")
    return proc, job


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


# ------------------------------------------------------------------ GUI
def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("OSS Flow: design and verification")
    root.geometry("980x760")
    state = {"project": None, "flow": None, "run": None, "proc": None, "lines": []}
    q = queue.Queue()

    proj_var = tk.StringVar(value="(no project yet: Browse or New project)")
    flow_var = tk.StringVar(value="")
    test_var = tk.StringVar()
    seed_var = tk.StringVar(value="1")
    verb_var = tk.StringVar(value="UVM_MEDIUM")
    waves_var = tk.BooleanVar(value=False)
    fmt_var = tk.StringVar(value="vcd")
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

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")
    ttk.Label(top, text="Project").pack(side="left")
    ttk.Entry(top, textvariable=proj_var, state="readonly").pack(side="left", fill="x", expand=True, padx=6)
    ttk.Button(top, text="Browse", command=lambda: browse()).pack(side="left")
    ttk.Button(top, text="New project", command=lambda: new_project()).pack(side="left", padx=4)
    ttk.Button(top, text="Terminal here", command=lambda: terminal_here()).pack(side="left")
    ttk.Label(root, textvariable=flow_var, padding=(10, 0)).pack(anchor="w")

    body = ttk.Frame(root, padding=8)
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

    out = tk.Text(root, height=16, wrap="none", font=("Consolas", 10))
    out.tag_configure("good", foreground="#1a7f37")
    out.tag_configure("bad", foreground="#c62828")
    out.tag_configure("warn", foreground="#b26a00")
    out.tag_configure("cmd", foreground="#555555")
    out.pack(fill="both", expand=True, padx=8)
    bottom = ttk.Frame(root, padding=8)
    bottom.pack(fill="x")
    ttk.Label(bottom, textvariable=cmd_var).pack(side="left")
    ttk.Button(bottom, text="Stop", command=lambda: stop()).pack(side="right")
    ttk.Button(bottom, text="Clean project (make clean)", command=lambda: clean_project()).pack(side="right", padx=4)
    ttk.Button(bottom, text="Clear output (like 'clear')", command=lambda: out.delete("1.0", "end")).pack(side="right")
    ttk.Label(bottom, textvariable=status_var).pack(side="right", padx=10)

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

    # ---- running make in a thread, output through the queue
    def run(args, after=None):
        if not need_project() or busy():
            return
        cmd_var.set("Command used: make {}   (in {})".format(args, state["run"]))
        status_var.set("Running ...")
        state["lines"] = []
        out.insert("end", "\n$ make {}\n".format(args), "cmd")
        out.see("end")

        def work():
            try:
                proc, job = start_make(state["run"], args)
                state["proc"], state["job"], state["stopped"] = proc, job, False
                for line in proc.stdout:
                    q.put(("line", line.rstrip("\r\n")))
                rc = proc.wait()
                job.close()
                q.put(("done", (rc, after)))
            except OSError as exc:
                q.put(("line", "Could not start the tools: {}".format(exc)))
                q.put(("done", (1, None)))
        threading.Thread(target=work, daemon=True).start()

    def pump():
        try:
            while True:
                kind, data = q.get_nowait()
                if kind == "line":
                    state["lines"].append(data)
                    out.insert("end", data + "\n", line_tag(data))
                    out.see("end")
                else:
                    rc, after = data
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
            for n in ("code_coverage.html", "functional_coverage.html"):   # created by this launcher
                f = state["run"] / n
                if f.exists():
                    f.unlink()
            run("clean")

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
        f = filedialog.askopenfilename(parent=root, title="Open a file in gvim",
                                       initialdir=str(state["project"] / sub), filetypes=ext)
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
                "basic": "Basic flow: design files .v or .sv; testbench files .sv."}[state["flow"]]
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

    def open_log():
        if not need_project():
            return
        run_dir, flow, t = state["run"], state["flow"], test_var.get()
        if flow == "design":
            names = ["flow_report.txt", "sim_report.txt", "lint_report.txt", "synth_report.txt"]
        elif flow == "basic":
            names = ["{}.log".format(t), "TC1.log", "synth.log"]
        else:
            names = ["logs/{}.log".format(t), "synth.log"]
        files = [run_dir / n for n in names if (run_dir / n).exists()]
        if not files:
            info("No log yet. Run a step first.")
            return
        open_with(GVIM, files[0])

    def waveform():
        if not need_project():
            return
        flow = state["flow"]
        if flow == "design":
            f, hint = state["run"] / "dump.vcd", "Click Simulate first."
        elif flow == "basic":
            f, hint = state["run"] / "waves.vcd", "Tick 'Save waveform' and click Run test first."
        else:
            f = state["run"] / "waves_{}.{}".format(test_var.get(), fmt_var.get())
            hint = "Tick 'Save waveform' and click Run test first."
        if not f.exists():
            info("{} not found. {}".format(f.name, hint))
            return
        open_with(SURFER, f)

    def terminal_here():
        where = state["run"] or Path(ENV["HOME"])
        subprocess.Popen([str(TERMINAL_CMD)], cwd=str(where), creationflags=NEW_CONSOLE)

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
        button(write_row, "Lint", lambda: run("lint"))
        if flow == "uvm":
            button(write_row, "Lint testbench", lambda: run("lint_tb"))
        opts_row.pack(fill="x")
        btn_row.pack(fill="x", pady=4)
        res_btn_row.pack(fill="x", pady=4)
        if flow == "design":
            button(btn_row, "Simulate", lambda: run("sim"))
            button(btn_row, "Waveform", waveform)
            button(btn_row, "Synthesize", lambda: run("synth"))
            button(btn_row, "Schematic", lambda: run("schematic", lambda: open_default(rd / (top_name() + "_rtl.svg"))))
            button(btn_row, "Gate schematic", lambda: run("schematic", lambda: open_default(rd / (top_name() + "_synth.svg"))))
            button(btn_row, "FSM diagram", lambda: run("fsm", lambda: open_default(rd / (top_name() + "_fsm.svg"))))
            button(res_btn_row, "Full report", lambda: run("report"))
            button(res_btn_row, "Open log", open_log)
            return
        tests = tests_from(rd)
        if tests:
            test_var.set(tests[0])
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
        if flow != "basic":
            ttk.Radiobutton(opts_row, text="VCD", variable=fmt_var, value="vcd").pack(side="left")
            ttk.Radiobutton(opts_row, text="FST", variable=fmt_var, value="fst").pack(side="left")
            button(btn_row, "Run test", lambda: run("run " + run_args()))
        else:
            button(btn_row, "Run test", lambda: run(test_var.get() + (" WAVES=1" if waves_var.get() else "")))
        button(btn_row, "Regression", lambda: run("regress"))
        button(btn_row, "Waveform", waveform)
        if has_target(rd, "synth"):
            button(btn_row, "Synthesize", lambda: run("synth"))
        button(btn_row, "Open log", open_log)
        ttk.Label(btn_row, text="(FSM diagram and schematic: use a Design flow project)").pack(side="left", padx=8)
        cov_row.pack(fill="x", before=res_btn_row)
        for k in COV_KINDS:
            box = ttk.Frame(cov_row, padding=(6, 2))
            box.pack(side="left")
            ttk.Label(box, text=k).pack()
            ttk.Label(box, textvariable=cov_vars[k], font=("Segoe UI", 12, "bold")).pack()
        ttk.Label(cov_row, text="(click Coverage after running tests)").pack(side="left", padx=10)
        cov_target = "covtxt" if flow == "basic" else "cov"

        def reports(which):
            code, func = write_coverage_html(rd)
            if not code:
                info("No coverage data yet. Run tests first, then try again.")
                return
            open_default(code if which == "code" else func)
        button(res_btn_row, "Coverage", lambda: run(cov_target))
        button(res_btn_row, "Code coverage report", lambda: run("covhtml", lambda: reports("code")))
        if flow != "basic":
            button(res_btn_row, "Functional coverage report", lambda: run(cov_target, lambda: reports("func")))
        button(res_btn_row, "Line-by-line (HTML)",
               lambda: run("covhtml", lambda: open_default(rd / "cov_html" / "index.html")))
        button(res_btn_row, "Uncovered lines", lambda: open_default(rd / "cov_annot"))
        if flow == "uvm":
            ttk.Label(res_btn_row, text="First UVM build: 6-8 minutes, about 3.5 GB RAM").pack(side="left", padx=10)

    def set_project(path):
        flow, run_dir = detect(path)
        if not flow:
            warn("No simdir/Makefile or sim/Makefile found in\n{}".format(path))
            return
        state.update(project=Path(path), flow=flow, run=run_dir)
        proj_var.set(str(path))
        flow_var.set("Flow: {}   |   run folder: {}".format(FLOW_NAMES[flow], run_dir))
        for v in cov_vars.values():
            v.set("-")
        build_rows()

    def browse():
        d = filedialog.askdirectory(parent=root, title="Choose a project folder (it contains rtl/, tb/ and sim/ or simdir/)")
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
