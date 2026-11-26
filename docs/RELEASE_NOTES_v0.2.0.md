# v0.2.0: pilot release 2 (Windows 10/11, 64-bit)

Same tools as v0.1.0. This release improves the OSS Flow window and adds single-file runs.
You still do not need Linux, WSL, MSYS2 or admin rights.

## Download

- `install_oss_flow.cmd`: one-click installer. It downloads the ZIP, checks it, installs to `C:\oss_flow_bundle`
  and runs a self-test. An existing v0.1.0 installation is moved aside first, not deleted.
- `oss_flow_windows_v0.2.0.zip`: all tools (about 1.3 GB after unzipping)
- `oss_flow_windows_v0.2.0.zip.sha256`: checksum. Compare it before unzipping by hand (see docs/INSTALL.md).

## What is new

- **Results open inside the window**, in tabs below the buttons: Console, Log, Report, Coverage (code and
  functional, coloured), Schematic, FSM, and a built-in **Waveform** viewer for VCD files (zoom, scroll, cursor).
- **Single file tab**: **New file...** (Verilog, SystemVerilog or UVM, with a small working example), a **Type**
  box, and separate **Compile** and **Simulate** buttons, like `vcs` then `./simv`.
- **New commands** `vrun`, `svrun`, `uvmrun`: run one file like `vcs -R` or `qrun`, with `--compile`, `--sim`,
  `--lint`, `--waves`, `--cov`. They print `NOTHING WAS PRINTED` when the file has no testbench code.
- **Project tab**: SV and UVM projects have separate **Compile** (`make build`) and **Simulate** (`make sim`).
  Compile UVM once, then simulate many tests and seeds in seconds.
- The **Single file** and **Project** tabs each have their own result tabs. **Clear** empties all result tabs of
  the side you are on, waveform included. **Clean** runs `make clean` (Project) or deletes only the files made for
  the chosen file (Single file), and then clears the tabs.
- **Dark / Light console** switch, remembered per user.
- sv and uvm Makefile templates: new `make sim` target; `make run` is now `build` + `sim`.

## Tested

On the same Windows 11 PC with 7.7 GB RAM: the launcher self-test with UVM, the window check (both tabs, all
result tabs, separation, Clear, Clean, theme), single-file Verilog, SystemVerilog and UVM runs, and the installer
from the new ZIP. The details are in docs/TESTED.md.

## Known limits

- Pilot: not yet tested on other laptops, Windows 10, managed (Device Guard) PCs, or paths with spaces.
- UVM runs without its C/DPI part, so there is no register backdoor and no regex in `uvm_config_db`.
- A UVM build takes 4–8 minutes and needs about 4 GB of free RAM.
- The built-in waveform viewer reads VCD files up to 60 MB. Use **Open in Surfer** for FST or bigger files.
- The programs are not digitally signed, so Windows SmartScreen may ask for confirmation.
- The Graphviz and Surfer licence texts are not yet included in the bundle (links are in licenses/README.md).
