# v0.1.0: pilot release (Windows 10/11, 64-bit)

First release of the open-source Verilog design and verification flow for plain Windows.
You do not need Linux, WSL, MSYS2 or admin rights.

## Download

- `oss_flow_windows_v0.1.0.zip`: all tools (about 1.3 GB after unzipping)
- `oss_flow_windows_v0.1.0.zip.sha256`: checksum. Compare it before unzipping (see docs/INSTALL.md).

Unzip it to `C:\`, then double-click `C:\oss_flow_bundle\OSS_Flow.cmd` (window) or `Verification_Terminal.cmd` (terminal).

## What is inside

Icarus Verilog 13.0, Verilator 5.054, UVM 1800.2-2020 (Verilator fork, patched), Yosys 0.66, Graphviz 16.1.2,
Surfer 0.7.0, lcov 1.16, GCC 16.2.0, make 4.4.1, Python 3.14.10, z3 4.16.0, gvim/vim 9.2.
There are 4 Makefile templates (design, sv, uvm, basic), 4 examples, the OSS Flow window and a trainee guide.

## Tested

The flow was tested on one Windows 11 PC with 7.7 GB RAM: design flow, SV flow, UVM, coverage, waveforms, both
editors and the OSS Flow window. The details are in docs/TESTED.md.

## Known limits

- Pilot: it is not yet tested on other laptops, Windows 10, managed (Device Guard) PCs, or paths with spaces.
- UVM runs without its C/DPI part, so there is no register backdoor and no regex in `uvm_config_db`.
- A UVM build takes 6–8 minutes and needs about 4 GB of free RAM.
- The programs are not digitally signed, so Windows SmartScreen may ask for confirmation.
- The Graphviz and Surfer licence texts are not yet included in the bundle (links are in licenses/README.md).
