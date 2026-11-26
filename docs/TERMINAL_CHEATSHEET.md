# Terminal cheat sheet (OSS Flow on Windows)

Open the terminal: desktop shortcut **Verification Terminal**, or **Terminal here** in the OSS Flow window
(Project tab: the project's run folder; Single file tab: the chosen file's folder). The prompt shows `OSS Flow`.
All tools are on PATH in that window only. `make help`, `svrun --help` and `vrun --help` list everything.

```bash
mkdir -p ~/vlsi_work && cd ~/vlsi_work     # your work folder = C:\Users\<you>\vlsi_work (no spaces in names)
gvim file.sv &                             # editor window   (or: vi file.sv   ->  i  type  Esc  :wq)
```

## 1. Single files, no Makefile (like `vcs -R` / `qrun`)

| Step | Verilog `.v` (Icarus) | SystemVerilog / SVA `.sv` (Verilator) | UVM `.sv` (Verilator + UVM) |
|---|---|---|---|
| Compile | `vrun tb.v --compile` | `svrun tb.sv --compile` | `uvmrun tb.sv --compile` (first time 4–8 min) |
| Simulate | `vrun tb.v --sim` | `svrun tb.sv --sim` | `uvmrun tb.sv --sim +UVM_TESTNAME=my_test` |
| Both | `vrun tb.v` | `svrun tb.sv` | `uvmrun tb.sv +UVM_TESTNAME=my_test` |
| Lint (-Wall) | `vrun tb.v --lint` | `svrun tb.sv --lint` | `uvmrun tb.sv --lint` (about 15 s) |
| Waveform | TB has `$dumpfile("dump.vcd"); $dumpvars;` → run → `surfer dump.vcd &` | same, and add `--waves` when compiling | same as SV |
| Coverage | not available (Icarus has none) | `svrun tb.sv --cov` → `<name>_cov_report.txt`, `<name>_cov_annot/` | `uvmrun tb.sv --cov` |
| Assertions | immediate `assert` only | concurrent SVA always on; a failure gives `RESULT: FAIL` | same as SV |
| Several files | `vrun dut.v tb.v` | `svrun my_if.sv my_pkg.sv top.sv` (interfaces, packages, top) | same as SV |

Options for all three: `--top NAME`, `-DNAME=VAL`, `-I dir`, and any `+plusarg` (e.g. `+UVM_VERBOSITY=UVM_HIGH`).
Output next to your file: `<name>.log`; build folder `svrun_<name>/` or `<name>.out`.
`NOTHING WAS PRINTED` = you ran a design file alone: run the testbench, or list design + testbench together.

## 2. Design project (`.v`): sim → waves → lint → synth → schematic → FSM → report

```bash
cp -r /examples/design_seq_det . && cd design_seq_det/simdir
```

| Command | Does | Output |
|---|---|---|
| `make sim` | Icarus simulation | `sim_report.txt`, `dump.vcd` |
| `make waves` | sim, then open Surfer | |
| `make lint` | Verilator -Wall on the RTL | `lint_report.txt` (`make open_lint`) |
| `make synth` | Yosys synthesis | `synth_report.txt`, `synth_stat.txt`, `synth_out.v` |
| `make schematic` | RTL + gate schematics | `<top>_rtl.svg`, `<top>_synth.svg` (`make open_schematic`, `make open_synth_schematic`) |
| `make fsm` | FSM state diagram (set `DETECT`) | `<top>_fsm.svg` (`make open_fsm`) |
| `make report` | all of the above | `flow_report.txt` (`make open_report`) |
| `make clean` | delete generated files only | |

Own design: set `TOP`, `TB_TOP`, `DETECT` at the top of the Makefile. One module per file, file named after it.

## 3. SV verification project (`.sv` + SVA)

```bash
cp -r /examples/sv_project . && cd sv_project/sim
```

| Command | Does |
|---|---|
| `make lint` | lint RTL + SVA, then the testbench |
| `make build` | **compile** only |
| `make sim TEST=smoke SEED=1` | **simulate** only (no compile) → `logs/smoke.log` |
| `make run TEST=random SEED=3 WAVES=1` | compile + simulate, write `waves_random.vcd` (`WAVE_FMT=fst` for FST) |
| `make waves TEST=random` | open the waveform in Surfer |
| `make regress` | all tests, PASS/FAIL table |
| `make cov` | code + functional coverage → `cov_report.txt`, `cov_annot/`, `cov_covergroup/` |
| `make covhtml` / `make covopen` | HTML line coverage → `cov_html/index.html`, open in browser |
| `make synth` | Yosys synthesis of `RTL_TOP` |
| `make clean` | delete generated files only (`rtl/`, `tb/`, `sva/` kept) |

Assertions live in `sva/` and are attached with `bind`; a failing `assert property` is printed in the log and the
test is FAIL. `cover property` hits appear in the coverage report.

## 4. UVM project

```bash
cp -r /examples/uvm_project . && cd uvm_project/sim
```

| Command | Does |
|---|---|
| `make lint` / `make lint_tb` | lint RTL + SVA / the whole UVM testbench |
| `make build` | **compile** once (4–8 min, about 4 GB RAM) |
| `make sim TEST=alu_smoke_test` | **simulate** only, seconds |
| `make sim TEST=alu_random_test SEED=7 VERBOSITY=UVM_HIGH WAVES=1` | other test / seed / verbosity, still no compile |
| `make waves TEST=alu_random_test` | open the waveform |
| `make regress` | all tests, PASS/FAIL table |
| `make cov` / `make covhtml` / `make covopen` | coverage, as in SV |
| `make clean` | delete generated files only |

PASS/FAIL comes from the log: `UVM_ERROR`/`UVM_FATAL` count > 0 means FAIL even if the program exits normally.

## 5. Everyday shell

| Command | Does |
|---|---|
| `pwd`, `ls`, `cd folder`, `cd ..`, `cd ~/vlsi_work` | where am I, list, move |
| `mkdir -p name`, `cp -r src dst`, `mv a b` | make folder, copy, move/rename |
| `cat file`, `less file` (`q` quits), `tail -f logs/smoke.log` | read files |
| `grep -n "UVM_ERROR" logs/*.log` | search in files |
| `clear`, `Ctrl+C` (stop a run), `exit` | clear screen, stop, close |
| `explorer .` | open this folder in Windows Explorer |
