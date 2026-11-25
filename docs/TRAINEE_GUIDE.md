# Open-Source Verilog Design & Verification Flow on Windows: Trainee Guide

Version v0.1.0 (pilot). Every command below was run exactly as written on one Windows 11 PC (Nov 2026).
Opening windows (Surfer, browser, gvim) was checked by eye. Installation: [INSTALL.md](INSTALL.md).

This guide uses one folder of free tools (the "bundle"). It covers the full flow:

- **Part A: Design (Verilog, `.v` files)**: write the RTL and testbench, simulate, check the waveform,
  lint and fix, synthesize, view the schematic, view the FSM state diagram, and get one report.
- **Part B: Verification (SystemVerilog, `.sv` files)**: simulate, read the output and waveforms,
  check code coverage, functional coverage and assertions.
- **Part C: UVM**: run UVM tests with all metrics.

---

## 0. Start the tools

1. Open the tools folder (`C:\oss_flow_bundle`, see [INSTALL.md](INSTALL.md)) and **double-click `Verification_Terminal.cmd`**.
   A terminal window opens with all the tools ready. Nothing is installed or changed on your PC.
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
   - **Clear output** empties the window (like `clear`).
   - **Clean project** runs `make clean`: it deletes only generated files, and your `rtl/`, `tb/` and `sva/`
     files are kept.
   - **Terminal here** opens the terminal in the project's run folder.
6. The bottom line always shows the real command, for example `Command used: make regress`.
   Type the same command in the terminal and you get the same result.

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

### B3. Simulate one test, then all tests

```bash
make run TEST=smoke
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

### C4. One test with options, and waveforms

```bash
make run TEST=alu_random_test SEED=7 WAVES=1
make waves TEST=alu_random_test
```

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
