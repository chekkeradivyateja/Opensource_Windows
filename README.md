# Open-Source Verilog Design & Verification Flow for Windows

A free replacement for paid simulators (VCS, Questa, Verdi) for **training**, on **plain Windows 10/11**.
You download one folder of tools, unzip it, and double-click. You don't need Linux, WSL, a virtual machine,
MSYS2, or admin rights.

| Flow | Steps |
|---|---|
| **Design (Verilog `.v`)** | write RTL + testbench → simulate → waveform → lint (fix, repeat) → synthesis → schematic → FSM state diagram → one report |
| **Verification (SystemVerilog `.sv`)** | simulate → output log → waveform → code coverage → functional coverage → assertions |
| **UVM** | UVM tests and regressions with coverage, assertions and waveforms |

There are three ways to work, and you can mix them freely:

| Start | What you get |
|---|---|
| `Verification_Terminal.cmd` | a terminal with all tools: `vi`, `gvim`, `make sim`, `make regress`, ... (industry style) |
| `OSS_Flow.cmd` | the **OSS Flow** window: buttons for every step, PASS in green and FAIL in red, coverage reports in the browser |
| `gvim` / `vi` | editors with Verilog/SystemVerilog colours |

> **Status: v0.3.0 = pilot release.** It is tested on one Windows 11 PC (see [docs/TESTED.md](docs/TESTED.md)).
> It is not yet tested on other trainee laptops. Please report problems (see [Getting help](#getting-help)).

---

## 1. System requirements

All numbers were **measured** on the test PC: Windows 11, Intel Core 3 100U (6 cores), **7.7 GB RAM**.
On other PCs they will differ. Slower disks and antivirus scanning make builds slower.

### 1.1 Your PC

| | Minimum | Recommended | Why |
|---|---|---|---|
| Windows | 10 (version 1803 or newer) or 11, **64-bit** on Intel/AMD | Windows 11 | the tools are 64-bit Windows programs; ARM laptops are not supported |
| RAM | **8 GB** | **16 GB** | a UVM build needs about **3.2–3.6 GB** at its peak; design and SV flows need less than 1 GB |
| Free disk | **5 GB** (the installer itself needs 3 GB) | **15 GB** | tools 1.3 GB + download 0.42 GB + your projects (see 1.3) |
| CPU | any 64-bit Intel/AMD | 4+ cores | builds use one core (`JOBS=1`) to save RAM; only a 6-core CPU was tested |
| Screen | 1366 × 768 | 1920 × 1080 | the OSS Flow window is about 980 × 760 |
| Admin rights | **not needed** | | everything stays in one folder and your user folder |
| Internet | once, for the download | | offline install from USB also works |

Check your PC: Settings → System → About. *System type* must say **64-bit operating system, x64-based processor**.
Or run `install_oss_flow.cmd --check`, which tests everything and changes nothing.

### 1.2 RAM and time per step

| Flow | Step | Time | Peak RAM (largest tool) |
|---|---|---|---|
| **Design** (Verilog) | `make sim` (Icarus) | 2 s | 7 MB |
| | `make lint` (Verilator) | 1 s | 16 MB |
| | `make synth` (Yosys) | 3 s | 16 MB |
| | `make schematic` / `make fsm` (Graphviz) | 2 s each | 27 MB |
| | `make report` (all steps) | 5 s | 16 MB |
| **SystemVerilog** | `make lint` | 2 s | 16 MB |
| | first `make run` (builds the simulator) | **20 s** | **584 MB** |
| | more tests with the same build (`make regress`) | 3–5 s | small |
| | switching waveform format VCD ↔ FST (rebuild) | 18 s | 582 MB |
| | `make covhtml`, `make synth` | 1–3 s | 16 MB |
| **UVM** | `make lint_tb` | 7 s | 636 MB |
| | first `make run` / `make regress` (**builds UVM + your testbench**) | **4–8 min** | **3.2–3.6 GB** |
| | more tests with the same build | about 3 s each | small |
| | `make covhtml` | 3 s | 16 MB |

Any change to a `.v` or `.sv` file means a new build in the SV and UVM flows. In the design flow, each step is so
quick that this doesn't matter.

### 1.3 Disk space for your projects

Plan for these sizes.

| Project type (examples) | Your source files | After running the full flow | After `make clean` |
|---|---|---|---|
| Design project (`design_seq_det`) | a few KB | **about 0.2 MB** (sim output, `dump.vcd`, reports, schematics) | sources only |
| SV project (`sv_project`) | a few KB | **about 3.5 MB** (mostly the `obj_dir` build folder) | sources only |
| UVM project (`uvm_project`) | about 10 KB | **about 0.9 GB** (the `obj_dir` build folder holds the compiled UVM library) | sources only |

**Waveforms grow with your design and the simulation length.** The example `dump.vcd` is 77 KB for about 1,000
clock cycles of a tiny design. A design with 100× more signals running 100× longer can easily produce a VCD file of
**several hundred MB**. To keep waveforms small:
- use `WAVE_FMT=fst` in the SV/UVM flows (FST is a compressed format and smaller than VCD)
- dump only the signals you need
- shorten long simulations while debugging

**Example plan for a course** (one trainee):

| Work | Count × size | Disk |
|---|---|---|
| Tools + kept download | | about 1.7 GB |
| Design labs | 30 × 0.2 MB | about 6 MB |
| SV labs | 15 × 3.5 MB | about 50 MB |
| UVM labs, **if every build is kept** | 5 × 0.9 GB | about 4.5 GB |
| UVM labs, **with `make clean`** after finishing each one | | under 1 MB |
| Waveforms | depends on your simulations | 0.1–2 GB |
| **Total** | | **about 3–9 GB**, so keep **15 GB free** |

Free space with `make clean` (or the launcher's **Clean project** button) in projects you have finished. It deletes
only generated files; your `rtl/`, `tb/` and `sva/` files stay. You may also delete the downloaded ZIP in
`%TEMP%\oss_flow_download` (0.42 GB) after installing.

### 1.4 What files you add, and what the flow creates

Keep each project in its own folder under `C:\Users\<you>\vlsi_work\`. Use names **without spaces**. Don't put
projects in OneDrive or on a network drive. **The file name must equal the module name**: `alu.v` holds `module alu`.

| | You write (keep these, back them up) | The flow creates (safe to delete with `make clean`) |
|---|---|---|
| **Design** project | `rtl/*.v` (design), `tb/*_tb.v` (testbench), `simdir/Makefile` (copied from `templates/design`) | `sim.out`, `dump.vcd` (waveform), `sim_report.txt`, `lint_report.txt`, `synth_report.txt`, `synth_stat.txt`, `synth_out.v` (netlist), `*_rtl.svg` / `*_synth.svg` (schematics), `*_fsm.svg` (FSM diagram), `flow_report.txt` (one report) |
| **SV** project | `rtl/*.v` or `*.sv`, `sva/*.sv` (assertions), `tb/*_pkg.sv` + `tb/tb_top.sv`, `sim/Makefile` (from `templates/sv`) | `obj_dir/` (build), `logs/<test>.log`, `cov/*.dat`, `cov_report.txt`, `cov_annot/`, `cov_covergroup/`, `cov_html/` (coverage), `waves_<test>.vcd/.fst`, `synth.log` |
| **UVM** project | `rtl/*`, `tb/*_if.sv`, `tb/*_pkg.sv` (UVM classes), `tb/tb_top.sv`, `sim/Makefile` (from `templates/uvm`) | the same as SV, plus a much bigger `obj_dir/` (about 0.9 GB) |

The OSS Flow window also writes `code_coverage.html` and `functional_coverage.html` (coverage reports) into the
`sim/` folder. They're removed by **Clean project**.

More details: [docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md).

## 2. Install (about 10 minutes)

**One click (recommended):** download **`install_oss_flow.cmd`** from the
[Releases](https://github.com/chekkeradivyateja/Opensource_Windows/releases) page and double-click it. It does the
following:
1. checks your PC
2. downloads and verifies the tools
3. installs them to `C:\oss_flow_bundle`
4. creates desktop shortcuts
5. runs a self-test

It needs no admin rights and deletes nothing. Options include `--check`, offline `--zip FILE` and `--uninstall`;
see [docs/INSTALL.md](docs/INSTALL.md).

**Manual:**
1. Open the **[Releases](https://github.com/chekkeradivyateja/Opensource_Windows/releases)** page and download
   `oss_flow_windows_v0.3.0.zip` and `oss_flow_windows_v0.3.0.zip.sha256`.
2. **Check the download.** In PowerShell, in your Downloads folder:
   ```powershell
   (Get-FileHash .\oss_flow_windows_v0.3.0.zip -Algorithm SHA256).Hash
   ```
   The result must equal the value in the `.sha256` file (upper or lower case does not matter).
   If it is different, delete the zip and download it again.
3. **Unzip** it to `C:\` (right-click → *Extract All...* → `C:\`). You get `C:\oss_flow_bundle`.
   Use a short path **without spaces**.
4. **Start:** double-click `C:\oss_flow_bundle\OSS_Flow.cmd` (window) or `Verification_Terminal.cmd` (terminal).
   Tip: double-click `Make_Shortcuts.cmd` for desktop and Start-menu shortcuts with icons, which you can pin
   to the taskbar.
5. **Check it works:** follow "First run" in [docs/INSTALL.md](docs/INSTALL.md#5-first-run-check). It takes 2 minutes.

To uninstall, delete the folder `C:\oss_flow_bundle`. Nothing else is changed on your PC.
Detailed step-by-step instructions: [docs/INSTALL.md](docs/INSTALL.md).

## 3. Use it

The trainee guide is [docs/TRAINEE_GUIDE.md](docs/TRAINEE_GUIDE.md). It covers every step of the design flow, the SV
flow and UVM, with commands you can copy. All terminal commands on one page:
[docs/TERMINAL_CHEATSHEET.md](docs/TERMINAL_CHEATSHEET.md).

Shortest possible start (terminal):
```bash
mkdir -p ~/vlsi_work && cd ~/vlsi_work
cp -r /examples/design_seq_det .
cd design_seq_det/simdir
make sim          # simulate  -> PASS: all checks passed
make waves        # waveform in Surfer
make lint         # lint      -> Lint passed
make synth        # synthesis
make open_fsm     # FSM state diagram in the browser
make report       # one report for the whole flow
```

Shortest possible start (window): double-click `OSS_Flow.cmd`, click **New project**, choose `design_seq_det`,
then click **Simulate**, **Waveform**, **Lint**, **Synthesize**, **Schematic**, **FSM diagram**.

## 4. Tools inside

| Tool | Version | Used for |
|---|---|---|
| Icarus Verilog | 13.0 | Verilog simulation (design flow) |
| Verilator | 5.054 | lint, SystemVerilog/UVM simulation, assertions, coverage |
| UVM | IEEE 1800.2-2020 (Accellera 2020.3.1, Verilator fork) | UVM testbenches |
| Yosys | 0.66 | synthesis, schematics, FSM extraction |
| Graphviz | 16.1.2 | drawing schematics and FSM diagrams |
| Surfer | 0.7.0 | waveform viewer (VCD, FST) |
| lcov / genhtml | 1.16 | HTML line-coverage report |
| GCC / make / Python / z3 / perl | 16.2.0 / 4.4.1 / 3.14.10 / 4.16.0 / 5.44.0 | needed by Verilator and the flow |
| gvim / vim (vi) | 9.2 | code editors |

Sources, licences and checksums: [docs/TOOLS.md](docs/TOOLS.md).

## 5. Repository contents

```
README.md                  this page
install_oss_flow.cmd       one-click installer (check, download + SHA-256, install, shortcuts, self-test)
OSS_Flow.cmd               starts the OSS Flow window
Verification_Terminal.cmd  starts the terminal with all tools
launcher/oss_flow.py       the OSS Flow window (Python, standard library only)
templates/                 Makefile templates: design/, sv/, uvm/, basic/
examples/                  design_seq_det (Verilog FSM), counter, sv_project (SVA + coverage), uvm_project
docs/                      INSTALL, SYSTEM_REQUIREMENTS, TRAINEE_GUIDE, TERMINAL_CHEATSHEET, TOOLS, TROUBLESHOOTING,
                           TESTED, MAINTAINER_BUILD
licenses/                  licence information for the shipped tools
VERSIONS.txt               exact version + checksum of every tool in the release bundle
```

The tools themselves (about 1.3 GB) are **not** in this repository. They are in the release ZIP.
The ZIP also contains the launcher, start scripts, templates, examples, trainee guide and `VERSIONS.txt`.

## 6. Limits compared with paid tools

- Verilator is **2-state**: there are no X/Z values in SV/UVM simulation. Icarus (design flow) is 4-state.
- UVM runs **without its C/DPI part** on Windows: register backdoor access and regex in `uvm_config_db` are not
  available. Normal agent/env/sequence/scoreboard testbenches work.
- A UVM build takes **6–8 minutes** after each change to the testbench or design.
- There is no single coverage database or Verdi-style debugger.
  The HTML line view shows line coverage only; the launcher's code and functional coverage reports show the rest.

More: [docs/TRAINEE_GUIDE.md#limits-compared-with-paid-tools-vcs-questa-verdi](docs/TRAINEE_GUIDE.md).

## Getting help

1. Read [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
2. Open an issue on this repository with: your Windows version, the exact command or button, and the full error
   text (copy it from the window or the log). Do not post passwords or personal data.

## Licence

The files in this repository are under the MIT licence (see `LICENSE`).
The tools in the release bundle keep their own licences (GPL, LGPL, Apache-2.0, EPL-2.0, EUPL-1.2, ISC, MIT,
Vim licence, ...). See [docs/TOOLS.md](docs/TOOLS.md) and [licenses/](licenses/).
