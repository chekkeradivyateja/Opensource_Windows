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

> **Status: v0.1.0 = pilot release.** It is tested on one Windows 11 PC (see [docs/TESTED.md](docs/TESTED.md)).
> It is not yet tested on other trainee laptops. Please report problems (see [Getting help](#getting-help)).

---

## 1. What your PC needs

| | Minimum | Recommended |
|---|---|---|
| Windows | 10 or 11, **64-bit** (x86-64) | Windows 11 |
| RAM | **8 GB** (all tests, including UVM, passed on a 7.7 GB PC) | 16 GB |
| Free disk | **3 GB** (download + unzipped tools) + space for projects (a UVM project build uses about **0.9 GB**) | 10 GB |
| CPU | any 64-bit Intel/AMD | 4 or more cores |
| Admin rights | **not needed** | |
| Internet | only once, to download | |

Full details: [docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md).

## 2. Install (about 10 minutes)

1. Open the **[Releases](https://github.com/chekkeradivyateja/Opensource_Windows/releases)** page and download
   `oss_flow_windows_v0.1.0.zip` and `oss_flow_windows_v0.1.0.zip.sha256`.
2. **Check the download.** In PowerShell, in your Downloads folder:
   ```powershell
   (Get-FileHash .\oss_flow_windows_v0.1.0.zip -Algorithm SHA256).Hash
   ```
   The result must equal the value in the `.sha256` file (upper or lower case does not matter).
   If it is different, delete the zip and download it again.
3. **Unzip** it to `C:\` (right-click → *Extract All...* → `C:\`). You get `C:\oss_flow_bundle`.
   Use a short path **without spaces**.
4. **Start:** double-click `C:\oss_flow_bundle\OSS_Flow.cmd` (window) or `Verification_Terminal.cmd` (terminal).
   Tip: right-click → *Send to → Desktop (create shortcut)*.
5. **Check it works:** follow "First run" in [docs/INSTALL.md](docs/INSTALL.md#5-first-run-check). It takes 2 minutes.

To uninstall, delete the folder `C:\oss_flow_bundle`. Nothing else is changed on your PC.
Detailed step-by-step instructions: [docs/INSTALL.md](docs/INSTALL.md).

## 3. Use it

The trainee guide is [docs/TRAINEE_GUIDE.md](docs/TRAINEE_GUIDE.md). It covers every step of the design flow, the SV
flow and UVM, with commands you can copy.

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
OSS_Flow.cmd               starts the OSS Flow window
Verification_Terminal.cmd  starts the terminal with all tools
launcher/oss_flow.py       the OSS Flow window (Python, standard library only)
templates/                 Makefile templates: design/, sv/, uvm/, basic/
examples/                  design_seq_det (Verilog FSM), counter, sv_project (SVA + coverage), uvm_project
docs/                      INSTALL, SYSTEM_REQUIREMENTS, TRAINEE_GUIDE, TOOLS, TROUBLESHOOTING,
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
