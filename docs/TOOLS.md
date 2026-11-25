# Tools in the release bundle

All versions are pinned. None is "latest". The licence column was read from the MSYS2 package database
(`pacman -Qi`) or from the official download page or licence file named in the Source column.

| Tool | Version | Role | Licence | Source |
|---|---|---|---|---|
| Verilator | 5.054 | lint, SV/UVM simulation, assertions, code coverage, functional coverage, VCD/FST | LGPL-3.0-only OR Artistic-2.0 | MSYS2 `mingw-w64-ucrt-x86_64-verilator` 5.054-1 (veripool.org/verilator) |
| Icarus Verilog | 13.0 | Verilog simulation (design flow) | GPL-2.0-or-later | MSYS2 `mingw-w64-ucrt-x86_64-iverilog` 1~13.0-2 |
| Yosys | 0.66 | synthesis, schematics, FSM extraction | ISC | MSYS2 `mingw-w64-ucrt-x86_64-yosys` 0.66-1 (yosyshq.net) |
| Graphviz | 16.1.2 | draws schematics and FSM diagrams (`dot`) | EPL-2.0 | graphviz.org official `windows_10_cmake_Release_Graphviz-16.1.2-win64.zip`, SHA-256 `0924501672e796e05d3b6dd402d518e352ed28e9329dc668f40ce52357aa9f4b` (= published) |
| Surfer | 0.7.0 | waveform viewer (VCD, FST) | EUPL-1.2 | gitlab.com/surfer-project/surfer `surfer_win_v0.7.0.zip`, SHA-256 `4fbb0ad93e1aa958f6944c036a8d01b36b267a96e7f904683317235cd041fc24` |
| UVM | IEEE 1800.2-2020, Accellera 2020.3.1 | UVM class library | Apache-2.0 | github.com/verilator/uvm @ `656f20d087370a7c742e00188d20bbf30fa95339` (archive SHA-256 `fd28a1b0a789376dd83c3903f4f06cc38d4e5969f64062bea36da8e88c0c07b8`), 2 lines patched (see below) |
| lcov / genhtml | 1.16 | HTML line-coverage report | GPL-2.0-or-later | MSYS2 `lcov` 1~1.16-2 (+ perl-json 4.11-2, perl-perlio-gzip 0.20-9) |
| GCC / g++ | 16.2.0 | compiles the C++ that Verilator generates | GPL-3.0-or-later WITH GCC-exception-3.1 | MSYS2 `mingw-w64-ucrt-x86_64-gcc` 16.2.0-7 |
| GNU make | 4.4.1 | runs the Makefiles | GPL-3.0 | MSYS2 `make` 4.4.1-3 |
| Python | 3.14.10 | Verilator build step; OSS Flow window (tkinter, Tcl/Tk 8.6.18) | PSF-2.0 (Tcl/Tk: Tcl licence) | MSYS2 `mingw-w64-ucrt-x86_64-python` 3.14.10-4 |
| z3 | 4.16.0 | constraint solver for `randomize()` | MIT | MSYS2 `mingw-w64-ucrt-x86_64-z3` 4.16.0-1 |
| perl | 5.44.0 | runs `verilator` and `genhtml` scripts | Artistic-1.0-Perl OR GPL-1.0-or-later | MSYS2 `perl` 5.44.0-1 |
| lz4 | 1.11.1 | needed for FST waveforms | BSD-2-Clause AND GPL-2.0-or-later | MSYS2 `mingw-w64-ucrt-x86_64-lz4` 1.11.1-2 |
| vim / vi | 9.2.1373 | terminal editor (`vi` starts `vim`) | Vim licence | MSYS2 `vim` 9.2.1373-1 |
| gvim | 9.2.1398 | window editor | Vim licence | github.com/vim/vim-win32-installer `gvim_9.2.1398_x64.zip`, SHA-256 `0161b9deb47f10c788e9965e1b2ca96604a2b0aed9e68b99c562ba806d8f3566` (= GitHub digest) |
| bash + MSYS2 runtime | 5.3.20 / 3.6.12 | the terminal and Unix tools (`cp`, `grep`, `sed`, ...) | GPL-3.0-or-later | MSYS2 `bash`, `msys2-runtime` |

## UVM patch (Windows and Verilator)

In `src/base/uvm_component.svh`:
- line 2608: `bit clone;` becomes `bit clone_flag;`
- line 2671: `wrapper.clone = clone;` becomes `wrapper.clone_flag = clone;`

UVM is compiled with `+define+UVM_NO_DPI` (no `--vpi`). The C/DPI part of UVM (`uvm_dpi.cc`) did not link
with this toolchain on Windows. As a result, register backdoor access (`uvm_hdl_*`) and regular-expression
matching in `uvm_config_db` are not available. Simple `*` wildcards still work.

## Windows-specific settings used by the Makefiles

| Setting | Why |
|---|---|
| C++ built with `-O1` (`-MAKEFLAGS "OPT_FAST=-O1 OPT_SLOW=-O1 OPT_GLOBAL=-O1"`) | the default `-Os` fails to link with GCC 16.2.0 (`undefined reference to std::__cxx11::basic_string(basic_string&&)`) |
| `sed -i 's/\r$//' coverage.info` before `genhtml` | `verilator_coverage` writes Windows line endings, which lcov cannot read |
| `UVM_HOME := $(shell cygpath -m "$(UVM_HOME)")` | Verilator is a native Windows program and needs `C:/...` paths for `+incdir+` |
| `pass/fail from the log` | a UVM simulation exits with 0 even when `UVM_ERROR` > 0 |

## What is left out of the bundle

These items are not shipped to keep the bundle small:
- the MSYS2 package manager (`pacman`) and its database
- manuals, docs and locales
- the Python test suite
- GHDL/LLVM/Ada (pulled in by the Yosys package, not used)
- the Verilator debug binary
- gvim's `install.exe`/`uninstall.exe`, which would change Windows settings
- GTKWave (Surfer is used instead)
