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
| OSS Flow window v0.2.0 | result tabs (Console, Log, Report, Coverage, Schematic, FSM, Waveform); Single file tab: New file, Type, Compile, Simulate for Verilog, SystemVerilog and UVM; Single file and Project results kept apart; Clear, Clean file outputs, make clean; dark/light console; tab heights (no buttons cut off) | PASS (window check script + checked on screen by the trainer) |
| OSS Flow Coverage tab: bins and details (after v0.3.0) | lab-style project after Run test: covergroup -> 5 coverpoints + 20-bin cross with HIT/MISSED and hit counts, covergroup 45.8 % = report; details windows for line (61 points, 7 missed), toggle (52, 20 missed), a module, the covergroup and the cross; `sv_project`: `alu_cg` 3 coverpoints + 12-bin cross all HIT, details for every type; no stale numbers when a project has no report; launcher self-test 53/53 | PASS (window check script + checked on screen by the trainer) |
| OSS Flow window, own Makefiles (after v0.3.0) | a lab-style Makefile (targets `TC1`-`TC3`, `regress_12/123`, `report_*`, `SIMULATOR` switch with a VERILATOR part): Browse to the project or its `sim/` folder; Test/Regression/Other target dropdowns filled from the Makefile, `*_VCS`/`*_Questa` hidden; Run test -> `make TC1 SEED1=77 SIMULATOR=VERILATOR` exit 0, Log tab `test1.log`, Coverage tab `urgReport1.txt`, FST waveform opens in Surfer; design/basic/sv/uvm examples still detected as before; launcher self-test 53/53 | PASS (window check script + checked on screen by the trainer) |
| OSS Flow window v0.3.0 | sharp at 150 % display scaling (DPI aware; window check reports 150 %, all tabs fit); Terminal here on the Single file tab; window icon | PASS (window check script + checked on screen by the trainer) |
| Shortcuts v0.3.0 | `Make_Shortcuts.cmd`: desktop + Start menu shortcuts start pythonw.exe / cmd.exe with icons; OSS Flow pinned to the taskbar and started from the pin | PASS (checked on screen by the trainer) |
| Terminal v0.3.0 | title "OSS Flow Terminal", prompt `OSS Flow <folder>`, tools still from the bundle (`MSYSTEM=UCRT64`) | PASS |
| Release ZIP v0.3.0 | 442,629,579 bytes, SHA-256 `6ab1bc80…529bcd27`; offline install with `install_oss_flow.cmd --zip` into a new folder: SHA-256 PASS, unpack PASS, launcher self-test 53/53 PASS (238 s in all); new files present, no test files | PASS |
| Release ZIP v0.2.0 | 442,607,824 bytes, SHA-256 `e245caf6…b3eea46`; offline install with `install_oss_flow.cmd --zip` into a new folder: SHA-256 PASS, unpack PASS, launcher self-test 53/53 PASS (174 s in all) | PASS |

## One-click installer (`install_oss_flow.cmd`)

All cases below were run on the test PC, with test folders under `C:\oss_inst_test`.

| Case | Expected | Result |
|---|---|---|
| `--check` | all checks shown, nothing changed | PASS (8/8 checks) |
| Wrong processor (ARM64), old Windows (build 16299), low disk (1 GB), no internet without `--zip`, path with a space, existing folder that is not OSS Flow, missing local ZIP | stop with a clear FAIL, nothing changed | PASS (7/7; nothing created) |
| Clean offline install (`--zip`) | checks, SHA-256, unpack, self-test | PASS: self-test 44/44, 201 s |
| Second run, same version | "already installed, nothing to do" | PASS: 3 s, file count unchanged (34,682) |
| Older version present, user answers No | nothing changed | PASS |
| Wrong checksum | stop **before** moving the old version | PASS |
| Unpack fails after the old version was moved | old version restored automatically | PASS |
| Older version present, user answers yes | old version moved to `_backup_<date>`, new version installed | PASS: self-test 44/44 |
| Shortcuts | desktop + Start menu: OSS Flow, Verification Terminal | PASS (target and start folder checked) |
| `--uninstall`: No / yes / again | nothing changed / shortcuts removed + folder moved to `_removed_<date>` / "nothing found" | PASS |
| Online install (download from the GitHub release) | download, SHA-256 matches, install, self-test | PASS: 442,618,481 bytes, self-test 44/44, 277 s |
| Second online install | reuse the downloaded ZIP (no new download) | PASS. The run took 21 min, compared with under 5 min before; the cause was not found (other load on the PC is possible) |

Not tested for the installer:
- **double-clicking** the downloaded `.cmd` in a browser download (SmartScreen prompt, the pause at the end)
- a PC without the developer tools
- a managed PC (Device Guard)
- a non-English Windows

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
