# System requirements

## Summary

| | Minimum | Recommended | Why |
|---|---|---|---|
| Operating system | Windows 10 (1803 or newer) or 11, **64-bit (x86-64)** | Windows 11 | the tools are 64-bit Windows programs |
| RAM | **8 GB** | 16 GB | a UVM build needs about **3.2–3.6 GB** at its peak |
| Free disk | **5 GB** (the installer itself needs 3 GB) | 15 GB | tools 1.3 GB + download 0.42 GB + projects; see the README, section 1.3 |
| CPU | any 64-bit Intel or AMD | 4+ cores | UVM builds use 1 core (`JOBS=1`) to keep RAM low |
| Admin rights | not needed | | everything runs from one folder |
| Internet | once, to download | | works offline afterwards |
| Screen | 1366 × 768 | 1920 × 1080 | the OSS Flow window is about 980 × 760 |

**Not supported:** 32-bit Windows, Windows on ARM (for example Snapdragon laptops), Windows 7/8, macOS, and Linux
(Linux has its own flow: [OpenSource_Ubuntu_Ver](https://github.com/chekkeradivyateja/OpenSource_Ubuntu_Ver)).

To check your PC: press **Win + Pause** (or Settings → System → About) and look at *System type*
(must say *64-bit operating system, x64-based processor*) and *Installed RAM*.

## Measured on the test PC

| Item | Value |
|---|---|
| PC | Windows 11 Pro (build 26200), Intel Core 3 100U (6 cores), **7.7 GB RAM** |
| Release ZIP | see the Releases page |
| Unzipped tools | about **1.3 GB** (about 30,000 files) |
| Design flow: each step (sim, lint, synth, schematic, FSM) | 1–3 s, peak RAM under 30 MB |
| Design flow: `make report` (all steps) | about 5 s |
| SV example: first build + test | about **20 s**, peak RAM **584 MB** |
| SV example: more tests with the same build | 3–5 s |
| UVM example: first build | **4–8 min** (228 s from `D:\`, up to 7.7 min under `C:\Users\...`), peak RAM **3.2–3.6 GB** |
| UVM example: more tests with the same build | about 3 s each |
| Disk after the full flow: design / SV / UVM project | about **0.2 MB** / **3.5 MB** / **0.9 GB** (`make clean` takes each back to its sources) |
| Example waveform | `dump.vcd`: 77 KB for about 1,000 cycles of a small FSM; it grows with the number of signals and the simulation length |

The full per-step table, the disk plan for a course, and the list of files you write and the flow creates are in the
[README](../README.md#1-system-requirements), section 1.

UVM builds were about 30% slower from a folder under `C:\Users\...` than from `D:\` on the test PC.
Antivirus scanning is a likely reason but this was not checked.

## Before a UVM build

- Close big programs (browser tabs, video calls) so that about 4 GB of RAM is free.
- Keep `JOBS=1` (the default). More parallel jobs need about 3 GB **each**.

## Company or college laptops

Some managed PCs block new programs ("blocked by your organization's Device Guard policy", "This app has been
blocked by your system administrator"). The flow compiles a **new program for every simulation**, so such a policy
can stop it. You cannot fix this yourself. Ask your IT team to allow programs in the tools folder and your project
folder, or use another PC. Do not try to bypass the policy.
