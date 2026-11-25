# What was tested, and what was not

Only real results are listed here. Tested on **one PC**:
- Windows 11 Pro, build 26200
- Intel Core 3 100U, **7.7 GB RAM**
- November 2026

| Area | Test | Result |
|---|---|---|
| Design flow | fresh `design_seq_det` (Moore "1011" FSM): sim 1016 checks / 0 errors, lint clean, synth (14 cells, 5 flip-flops), RTL + gate schematics, FSM diagram (10 transitions), report | PASS |
| Design flow, failure cases | unused signal → lint FAILED; wrong FSM transition → simulation FAILED; design without FSM → "No FSM found" | correctly detected |
| SV flow | `sv_project`: lint, regression (2 tests), seeds, VCD/FST waveforms, code coverage, functional coverage (covergroups 100%), SVA, synth | PASS |
| Basic flow | `counter`: TC1/TC2, waveforms, coverage, synth | PASS |
| UVM | `uvm_project`: lint, testbench lint, regression (2 tests), single test with seed/verbosity/waveform, coverage | PASS (build 6–8 min, peak about 3.4–3.6 GB) |
| UVM, failure case | adder environment with a deliberate +1 bug: 50/50 mismatches reported, UVM_ERROR 51 | correctly detected |
| Bundle only | everything above run through `Verification_Terminal.cmd` with **no other tools on PATH**: all tools came from the bundle | PASS |
| Different folder/drive | copies of the tool folder on `D:\` and under `C:\Users\...` | PASS |
| Editors | gvim and vi open, colour Verilog/SV, edit and save; simulation afterwards PASS | PASS (checked on screen) |
| OSS Flow window | all buttons, dialogs on top, Stop ends all processes, Clean keeps sources, coverage reports; built-in self-test 44/44 | PASS (window checked on screen) |
| Viewers | Surfer (VCD, FST), schematics and FSM in the browser, coverage HTML | PASS (checked on screen) |
| Trainee guide | every command run exactly as written | PASS |
| Release ZIP v0.1.0 | SHA-256 checked, unzipped into a new folder `C:\oss_ziptest`; INSTALL.md first-run commands (design `make report`, SV `make regress` + `covhtml`) and launcher self-test with UVM (49/49) all from the unzipped copy | PASS |

## NOT tested yet

- A PC that **never had MSYS2** installed. This was the closest possible test: all other tools were removed from PATH.
- Other Windows versions (Windows 10), other laptops, other antivirus products, or **company-managed PCs**
  (Device Guard / App Control may block the tools).
- User names or paths **with spaces**.
- The release ZIP downloaded through a browser. It was tested unzipped on the test PC only. SmartScreen may
  warn about the unsigned programs.
- Network drives and OneDrive folders.
- Larger designs, long UVM regressions, and RAM use above the examples.

**These will be checked in a pilot with a few trainees before wider use.**
