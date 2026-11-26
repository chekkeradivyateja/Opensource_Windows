# Open-Source Verilog Design & Verification Flow on Windows: Trainee Guide

Version v0.3.0 (pilot). Every command below was run exactly as written on one Windows 11 PC (Nov 2026).
Opening windows (Surfer, browser, gvim) was checked by eye. Installation: [INSTALL.md](INSTALL.md).

This guide uses one folder of free tools (the "bundle"). It covers the full flow:

- **Part A: Design (Verilog, `.v` files)**: write the RTL and testbench, simulate, check the waveform,
  lint and fix, synthesize, view the schematic, view the FSM state diagram, and get one report.
- **Part B: Verification (SystemVerilog, `.sv` files)**: simulate, read the output and waveforms,
  check code coverage, functional coverage and assertions.
- **Part C: UVM**: run UVM tests with all metrics.

---

## 0. Start the tools

0. Shortcuts: the installer puts **OSS Flow** (blue waveform icon) and **Verification Terminal** (black `>_`
   icon) on the desktop and in the Start menu. Missing? Double-click `C:\oss_flow_bundle\Make_Shortcuts.cmd`.
   To keep them on the taskbar: right-click the shortcut → **Show more options** → **Pin to taskbar**.
1. Open the tools folder (`C:\oss_flow_bundle`, see [INSTALL.md](INSTALL.md)) and **double-click `Verification_Terminal.cmd`**.
   A terminal window titled **OSS Flow Terminal** opens with all the tools ready. The prompt shows
   `OSS Flow` and your folder. Nothing is installed or changed on your PC, and you do not need MSYS2:
   the terminal (bash) and the tools are inside the bundle folder.
2. In this terminal:
   - `~` is your Windows user folder (`C:\Users\<you>`).
   - `/examples` and `/templates` are folders inside the bundle.
   - Drive letters look like `/c/...` and `/d/...`.
3. Typing tips:
   - **Type commands by hand.** Text pasted from Word or PDF can contain hidden characters.
   - Press **Tab** to complete file names.
   - Press **Up arrow** to repeat an earlier command.
   - Press **Enter** only at the end of a line.
   - Letters matter: `-O1` is the letter **O**; `cd ~` needs a **space**.

Create your own work folder once:

```bash
mkdir -p ~/vlsi_work
cd ~/vlsi_work
```

All terminal commands (single files, design, SV, UVM, shell basics) are on one page:
[TERMINAL_CHEATSHEET.md](TERMINAL_CHEATSHEET.md). Print it and keep it next to the keyboard.

## 1. Editors: gvim and vi

| Editor | Start it | Save and close |
|---|---|---|
| **gvim** (window, mouse, menus) | `gvim file.v` | File → Save, or type `:w` Enter; close the window |
| **vi** (in the terminal) | `vi file.v` | `Esc`, then `:wq` Enter |

Both show Verilog and SystemVerilog in colour.

vi basics: press `i` to start typing, `Esc` to stop, `:w` to save, `:q` to quit, `:q!` to quit
without saving, `u` to undo, `/word` to search, and `dd` to delete a line.

## 2. Three ways to work (mix them freely)

| Way | Start | Good for |
|---|---|---|
| **Terminal** | `Verification_Terminal.cmd` | learning the real commands (`vi`, `gvim`, `make ...`), as in industry |
| **OSS Flow launcher** | `OSS_Flow.cmd` | buttons instead of typing; PASS in green, FAIL in red |
| **gvim** | from the terminal (`gvim file.v`) or the launcher's **Edit** buttons | writing and saving code |

All three use the same project folders and the same Makefiles, so you can, for example, write the code in vi,
run `make sim` in the terminal, and then open the coverage report from the launcher.

**Launcher in short:**
1. **New project** creates a copy of an example in `~/vlsi_work/<name>`.
   **Browse** opens a project you already have.
2. **New file** asks for the module name and type (`.v` or `.sv`), creates the file and opens it in gvim.
   **Edit RTL** and **Edit testbench** open existing files. Save with **Ctrl+S**.
3. Click a step:
   - Design: **Simulate**, **Waveform**, **Lint**, **Synthesize**, **Schematic**, **Gate schematic**,
     **FSM diagram**, **Full report**.
   - SV/UVM: **Run test** (Test, Seed, Save waveform), **Regression**, **Waveform**, **Synthesize**.
4. Results:
   - **Open log**.
   - SV/UVM: **Coverage**, **Code coverage report**, **Functional coverage report** (covergroups, bins,
     cover properties), **Line-by-line (HTML)**, **Uncovered lines**.
5. Other buttons:
   - **Stop** ends a running step completely.
   - The **Single file** tab and the **Project** tab each have their own result tabs (Console, Log, Report,
     Coverage, Schematic, FSM, Waveform). A project run never shows up on the Single file side, and the
     other way round.
   - **Clear (all result tabs)** empties every result tab of the side you are on, waveform included
     (like `clear`). No files are deleted.
   - **Clean project (make clean)** (Project tab) runs `make clean` and then clears the Project result tabs.
     It deletes only generated files, and your `rtl/`, `tb/` and `sva/` files are kept.
   - **Clean file outputs** (Single file tab) lists the files `vrun`/`svrun`/`uvmrun` made for the chosen
     file (build folder, `.log`, `.out`, coverage files, its `.vcd`), asks you, deletes them and clears the
     Single file result tabs. Your source file is never touched.
   - **Dark console / Light console** switches the Console, Log and Report text between a dark terminal look
     and white. The choice is remembered for next time.
   - **Terminal here** opens the OSS Flow terminal in the project's run folder (Project tab) or in the
     chosen file's folder (Single file tab).
6. The bottom line always shows the real command, for example `Command used: make regress`.
   Type the same command in the terminal and you get the same result.
7. **Results open in tabs below the buttons**, inside the same window:

   | Tab | Shows |
   |---|---|
   | **Console** | live output of the running step |
   | **Log** | the simulation log of the last run (fills in automatically after Simulate) |
   | **Report** | lint report, synthesis statistics, full flow report |
   | **Coverage** | code coverage (overall, per module, per instance) and functional coverage (covergroup → coverpoint → bin, cover properties), coloured green / amber / red |
   | **Schematic** / **FSM** | RTL or gate schematic and the FSM diagram as pictures, with zoom |
   | **Waveform** | built-in VCD viewer: pick signals on the left, **Zoom in/out/Fit**, scroll, click in the waves for a cursor with values. **Open in Surfer** for FST files, big files or more features |

   Waveform tips: double-click a signal name to add it. Click a name, then **Remove**. Ctrl + mouse wheel zooms;
   Shift + mouse wheel scrolls in time.

## 3. Single files: quick tests like `vcs file.sv -R` or `qrun file.sv`

For small exercises (a class with constraints, an SVA example, a single-file UVM test), you don't need a project or
a Makefile. Put the file in a folder without spaces and run it directly.

**In the OSS Flow window (Single file tab):**
1. **New file...**: choose the folder (Browse), type the file name, and choose the type: **Verilog (.v)**,
   **SystemVerilog (.sv)** or **UVM (.sv)**. Keep "Start with a small working example" ticked, so you start from code
   that already prints something. The file opens in **gvim**.
   Or use **Choose file...** to pick an existing file.
2. Write your code in gvim and save it (**Ctrl+S**).
3. Click **Compile**, then **Simulate**. Your `$display` output appears in the **Console** tab, and the **Log** tab
   keeps a copy.
4. Click **Waveform** or **Coverage** to see those results in their tabs.

The **Type** box next to the file name decides the command. The window sets it automatically, and you can change it:

| Type | Command | Chosen automatically when |
|---|---|---|
| Verilog | **vrun** (Icarus Verilog) | the file ends in `.v` |
| SystemVerilog | **svrun** (Verilator) | a `.sv` file without UVM |
| UVM | **uvmrun** (Verilator + UVM library) | the file uses `uvm_pkg`, `uvm_macros.svh` or `extends uvm_...` |

If the Console shows `NOTHING WAS PRINTED`, the chosen file has no code that prints. A design file alone, like a
counter, does nothing by itself: choose the testbench file.

`uvmrun` is the same as `svrun --uvm`. `svrun` also finds UVM by itself, so both commands work for UVM files.

| You want | Terminal | OSS Flow window | Like |
|---|---|---|---|
| **Compile** only | `svrun my_file.sv --compile` / `vrun my_file.v --compile` | **Compile** | `vcs -sverilog my_file.sv` |
| **Simulate** only (the last compile, no compile) | `svrun my_file.sv --sim` / `vrun my_file.v --sim` | **Simulate** | `./simv` |
| Both | `svrun my_file.sv` / `vrun my_file.v` | **Compile + Simulate** | `vcs -R` / `qrun` |
| Lint (-Wall) | `svrun my_file.sv --lint` / `vrun my_file.v --lint` | **Lint** | |
| Edit the file | `gvim my_file.sv` | **Edit** | |
| Several files | `uvmrun my_if.sv my_pkg.sv top.sv --compile` (compile order: interfaces, packages, top) | terminal only | |
| UVM test name, seed and so on | `uvmrun tb.sv --sim +UVM_TESTNAME=my_test +UVM_VERBOSITY=UVM_HIGH` | type it in **Arguments**, then **Simulate** | `./simv +UVM_TESTNAME=...` |
| Waveform | compile with `--waves` (your code needs `$dumpfile`/`$dumpvars`), then `surfer dump.vcd` | `--waves` in **Arguments**, then **Open waveform...** | |
| Coverage | compile and simulate with `--cov` (prints code + functional coverage) | `--cov` in **Arguments** | |

**Typical UVM loop:** **Compile** once (several minutes), then **Simulate** as often as you like with different
`+UVM_TESTNAME`, seeds or verbosity (seconds each). After you change a file, **Compile** again.

- **The top module is found automatically**: it's the module that nothing else instantiates. If there are several,
  choose one with `--top NAME`.
- **UVM is detected automatically.** If the file uses `uvm_pkg`, `uvm_macros` or `extends uvm_...`, the UVM library
  is added. The first UVM build takes a few minutes; later runs of the same files reuse it.
- **Output:** the run is printed and saved in `<file name>.log`. The build folder is `svrun_<file name>/`.
- `svrun` and `vrun` print `RESULT: FAIL` when the run reports `%Error`, a failed assertion, `UVM_ERROR` or
  `UVM_FATAL`.

Example (a constraint exercise saved as `const_top.sv`):
```systemverilog
class test;
  rand int a;  real b;
  constraint c1 {a inside {[555:655]};}
  function void post_randomize; b = a/10.0; endfunction
endclass
module const_top;
  initial begin
    static test test_h = new();          // 'static' avoids the IMPLICITSTATIC lint warning
    repeat (10) begin
      assert(test_h.randomize() == 1);
      $display("The generated values are : %0p", test_h.b);
    end
  end
endmodule
```
```bash
svrun const_top.sv          # prints 10 values between 55.5 and 65.5
svrun const_top.sv --lint   # -Wall lint: only "b is not used" remains (lint can't see the read inside $display); harmless
```

> Don't put such files into an example project's `rtl/` folder. A project's Makefile builds only its own top
> (`tb_top`), so your file would be compiled but never run.

---

## Part A: Design flow (Verilog `.v`)

Project layout (every design project looks like this):

```
my_design/
  rtl/      design files, e.g. seq_det.v   (module seq_det lives in seq_det.v)
  tb/       testbench files, e.g. seq_det_tb.v
  simdir/   Makefile; all results appear here
```

**Rules:**
- The file name must equal the module name (`alu.v` holds `module alu`).
- The testbench must call `$dumpfile("dump.vcd")` and `$dumpvars`.
- The testbench must print `PASS: all checks passed` only when all of its checks pass.

### A1. Copy the example

```bash
cd ~/vlsi_work
cp -r /examples/design_seq_det .
cd design_seq_det/simdir
make help
```

The example is `seq_det`, a Moore FSM that detects the bit pattern 1011.

### A2. Write or change the code

```bash
gvim ../rtl/seq_det.v
gvim ../tb/seq_det_tb.v
```

### A3. Simulate (Icarus Verilog)

```bash
make sim
```

The result is good when the last lines show `checks=1016 errors=0` and `PASS: all checks passed`.
The log is saved to `sim_report.txt`, and the waveform to `dump.vcd`.
If you see `SIMULATION FAILED`, read `sim_report.txt`, fix the code, and run `make sim` again.

### A4. Check the waveform (Surfer)

```bash
make waves
```

Surfer opens `dump.vcd`. Add the signals `clk`, `din`, `dout` and `dut.state`, then check that
`dout` goes high one clock after each `1011`.

### A5. Lint (Verilator -Wall), fix, and repeat

```bash
make lint
```

- Good: `Lint passed: no warnings or errors`.
- Problem: lines starting with `%Warning-...` or `%Error-...` show the file and line number.
  For example: `%Warning-UNUSEDSIGNAL: ...seq_det.v:10:8: Signal is not used: 'spare_copy'`.
  Fix the code, then **run `make sim` and `make lint` again** until both pass.
- Note: Verilator ignores signals whose name contains `unused`, so don't name signals `unused_...`.

### A6. Synthesis (Yosys)

```bash
make synth
```

This prints the cell statistics (for the example: 14 cells including 5 flip-flops).
Files: `synth_report.txt` (full log), `synth_stat.txt` and `synth_out.v` (gate-level netlist).

### A7. Schematic (Yosys + Graphviz)

```bash
make schematic
make open_schematic
make open_synth_schematic
```

`seq_det_rtl.svg` is the RTL view, and `seq_det_synth.svg` is the view after synthesis.
They open in your browser.

### A8. FSM state diagram (only for FSM designs)

```bash
make fsm
make open_fsm
```

This draws `seq_det_fsm.svg`. The arrows are labelled with the input bit, and the states listed in
`DETECT` are drawn as double circles (state `100` in the example).
If the design has no FSM, you get `No FSM found` (that is normal).

### A9. One report for the whole flow

```bash
make report
gvim flow_report.txt
```

The summary shows PASSED or FAILED for Simulation, Lint, Synthesis, Schematic and FSM diagram.
`make report` ends with an error if any step FAILED.

### A10. Start your own design

```bash
mkdir -p ~/vlsi_work/my_design/rtl ~/vlsi_work/my_design/tb ~/vlsi_work/my_design/simdir
cp /templates/design/Makefile ~/vlsi_work/my_design/simdir/
cd ~/vlsi_work/my_design/simdir
gvim Makefile
```

In the `EDIT HERE` block, set `TOP` (design module), `TB_TOP` (testbench module) and `DETECT`.
Leave `DETECT` empty if your design has no FSM. Then follow steps A2 to A9.

---

## Part B: Verification flow (SystemVerilog `.sv`)

Project layout:

```
my_sv/
  rtl/   design (.sv / .v)
  sva/   assertion modules + bind statements (optional)
  tb/    *_pkg.sv packages, then the top testbench
  sim/   Makefile; all results appear here
```

**Testbench rules:**
- The testbench reads the test name from `+TEST=<name>` and prints `TEST PASSED` or `TEST FAILED`.
- For waveforms, it calls `$dumpfile`/`$dumpvars` when `+WAVES` is given (see the example).

### B1. Copy the example and look at the targets

```bash
cd ~/vlsi_work
cp -r /examples/sv_project .
cd sv_project/sim
make help
make check
```

### B2. Lint

```bash
make lint
```

Good: `LINT PASSED`.

### B3. Compile, simulate one test, then all tests

```bash
make build                   # Compile only (button: Compile)
make sim TEST=smoke          # Simulate only, no compile (button: Simulate)
make run TEST=smoke          # both (button: Compile + Simulate)
make regress
```

`make regress` prints a table (`smoke PASS`, `random PASS`) and `REGRESSION PASSED`.
The logs are in `logs/<test>.log`. Options: `make run TEST=random SEED=7`.

### B4. Waveforms

```bash
make run TEST=random WAVES=1 WAVE_FMT=fst
make waves TEST=random WAVE_FMT=fst
```

### B5. Coverage (code coverage + functional coverage)

```bash
make covhtml
make covopen
```

- The text summary shows line, toggle, branch and expression coverage (code coverage) and
  covergroup coverage (functional coverage).
- Details are in `cov_report.txt`, `cov_annot/` (lines never hit are marked `%00`) and `cov_covergroup/`.
- `make covopen` shows the HTML report (line coverage) in the browser.

### B6. Assertions (SVA)

The assertions in `sva/` are checked during every `make run` / `make regress`.
A failing assertion prints `%Error: ... Assertion failed`, and the test is then marked FAIL.

### B7. Synthesis of the design

```bash
make synth
```

### B8. Start your own SV project

Copy `/templates/sv/Makefile` into your `sim/` folder and edit the `EDIT HERE` block
(`TOP`, `RTL_TOP`, folders, `TESTS`).

---

## Part C: UVM

Before you start:
- A UVM build takes **about 6–8 minutes** and needs **about 3.5 GB of free RAM**.
  Close other programs before building. Every change to the testbench or design (or a different
  `WAVE_FMT`) means a new build; running more tests with the same build takes only seconds.
- Your test must print `TEST PASSED` in `report_phase`. The flow passes a test only when the log has
  `TEST PASSED`, `UVM_ERROR :    0` and `UVM_FATAL :    0`. Do not trust the exit code alone.

### C1. Copy the example

```bash
cd ~/vlsi_work
cp -r /examples/uvm_project .
cd uvm_project/sim
make help
make check
```

`make check` must show `UVM library: found`.

### C2. Lint

```bash
make lint
make lint_tb
```

### C3. Run all UVM tests (first build takes several minutes)

```bash
make regress
```

Good: `alu_smoke_test PASS`, `alu_random_test PASS`, `REGRESSION PASSED`.

### C4. Compile once, then simulate tests with options and waveforms

```bash
make build                                         # Compile once (several minutes)
make sim TEST=alu_smoke_test                       # Simulate: seconds, no compile
make sim TEST=alu_random_test SEED=7 WAVES=1       # another test/seed, still no compile
make waves TEST=alu_random_test
```
In the OSS Flow window: **Compile**, then choose the test, seed and verbosity, and click **Simulate**.

### C5. Coverage

```bash
make covhtml
make covopen
```

### C6. Start your own UVM project

Copy `/templates/uvm/Makefile` into your `sim/` folder and edit the `EDIT HERE` block
(`TOP`, `RTL_TOP`, `TESTS`; keep interfaces `*_if.sv` and packages `*_pkg.sv` in `tb/`).

---

## Troubleshooting

| You see | Meaning and fix |
|---|---|
| `command not found` | You are not in the Verification Terminal. Start it with `Verification_Terminal.cmd`. Also check the spelling. |
| `-bash: $'\302...': command not found` | Hidden characters from pasted text. Type the command by hand. |
| `No rule to make target` | Wrong folder. `cd` into `simdir/` (design) or `sim/` (SV/UVM). |
| `SIMULATION FAILED` / `FAIL` in a table | Your testbench checks failed. Read `sim_report.txt` or `logs/<test>.log`. |
| `%Warning-...` from `make lint` | Fix the line shown, then run sim and lint again. |
| `No FSM found` | The design has no state machine Yosys can extract. Normal for non-FSM designs. |
| `Cannot find include file` (UVM) | `make check` must show `UVM library: found`. Use the Verification Terminal. |
| UVM build very slow or the PC freezes | Not enough free RAM. Close programs and keep `JOBS=1`. |
| A program is blocked by Windows ("blocked by your organization") | Your PC blocks new programs. Ask your IT team. Do not try to bypass it. |

## Limits compared with paid tools (VCS, Questa, Verdi)

- Verilator is 2-state: there are no X or Z values in simulation.
- UVM runs without its C (DPI) part. Register backdoor access and regular-expression matching in
  `uvm_config_db` are not available. Normal agent/env/scoreboard testbenches work.
- The HTML coverage report shows line coverage. Other coverage types are in `cov_report.txt`.
- There is no single coverage database or debugger like Verdi.
- UVM builds take minutes, not seconds.
