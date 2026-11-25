# Troubleshooting

## Starting

| You see | What it means | What to do |
|---|---|---|
| Double-click on a `.cmd` does nothing / closes at once | the folder was moved or is incomplete | unzip again to `C:\oss_flow_bundle`; check the SHA-256 (INSTALL step 2) |
| "Windows protected your PC" (blue SmartScreen box) | Windows has not seen this file before | click **More info → Run anyway** only if you downloaded it from this project's Releases page and the checksum matched |
| "blocked by your organization", "blocked by your system administrator", "Device Guard" | your PC's IT policy blocks new programs | you cannot fix this yourself: ask IT, or use another PC. Do not try to bypass it |
| The antivirus removes or quarantines a file | false alarm on a compiler or tool file | ask IT/antivirus support to allow the tools folder; then unzip again |
| `make: command not found` / `'make' is not recognized` | you are in a normal PowerShell or Command Prompt | start `Verification_Terminal.cmd` (or use the OSS Flow window) |

## Typing in the terminal

| You see | Fix |
|---|---|
| `-bash: $'\302\226cd': command not found` or other strange characters | text pasted from Word/PDF contains hidden characters: type the command by hand |
| `cd~: command not found` | a space is missing: `cd ~` |
| `unrecognized command-line option '-0s'` | that is a zero, use the letter O: `-Os` / `-O1` |
| A long command does not work | it was split into two lines: press Enter only at the end; or use the OSS Flow window |
| `No rule to make target 'sim'` | wrong folder: `cd` into `simdir/` (design) or `sim/` (SV/UVM) |

## Simulation and lint

| You see | What it means | What to do |
|---|---|---|
| `SIMULATION FAILED (see sim_report.txt)` | your testbench checks failed, or it never printed `PASS: all checks passed` | read `sim_report.txt`; the testbench must print that exact line only when its checks pass |
| `Unknown module type: xyz` (Icarus) | file name is not the module name | `module xyz` must be in `rtl/xyz.v` (or `tb/xyz.v`) |
| `%Warning-...` from `make lint` | lint found a problem | fix the file and line shown; run `make sim` and `make lint` again |
| A signal named `unused_...` is not reported | Verilator ignores signals whose name contains `unused` | do not use that word in signal names |
| `== random: FAIL` in a table | the test printed TEST FAILED, an `%Error`, or (UVM) `UVM_ERROR` > 0 | open `logs/<test>.log` (button **Open log**) |
| `%Error: ... Assertion failed` | an SVA assertion failed: a real design or testbench bug | read the assertion name and time in the log |

## UVM

| You see | What it means | What to do |
|---|---|---|
| Build takes many minutes | normal: UVM is compiled with your testbench | wait (6–8 min); later runs with the same build are fast |
| PC very slow / build killed / `out of memory` | not enough free RAM | close programs; keep `JOBS=1`; at least 8 GB RAM needed |
| `Cannot find include file: 'uvm_macros.svh'` | UVM library not found | use `Verification_Terminal.cmd` or the OSS Flow window; `make check` must say `UVM library: found` |
| Two `UVM_WARNING`s: `NO_DPI_USED`, `NO_VISIT_CHECK` | expected on Windows (UVM runs without its C part) | ignore |
| The run "passes" but you expected a failure | the exit code of a UVM simulation is 0 even with UVM errors | the flow decides PASS/FAIL from the log (`TEST PASSED`, `UVM_ERROR : 0`); print `TEST PASSED` only when your scoreboard has no errors |

## Coverage, waveforms, schematics

| You see | What to do |
|---|---|
| Coverage numbers show `-` | run tests first, then click **Coverage** (or `make cov`) |
| `waves_<test>.vcd not found` | tick **Save waveform** (or `WAVES=1`) and run the test again |
| `No FSM found in <top>` | the design has no state machine Yosys can extract; normal for non-FSM designs |
| SVG/HTML opens in the wrong program | right-click an `.svg` → *Open with* → your browser → *Always* |

## The OSS Flow window

| You see | What to do |
|---|---|
| A dialog does not appear | check the taskbar; dialogs open on top of the OSS Flow window |
| **Stop** pressed | the whole run (make, compiler, simulation) is ended; start the step again |
| "A command is still running" | wait for it, or press **Stop** |
| A button is missing (e.g. Synthesize) | your project's Makefile is old: create a new project from the examples |

## Reporting a problem

Open an issue on the GitHub repository with:
1. Windows version (Settings → System → About),
2. what you clicked or typed,
3. the full error text (copy from the window or from the log file).

Do not include passwords or personal data.
