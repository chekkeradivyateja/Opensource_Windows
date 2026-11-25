# counter example

8-bit counter (`rtl/`) with a testbench (`tb/`) and the Makefile template (`sim/`).
Tested on 2026-11-20 with Verilator 5.054 on Ubuntu 24.04.5 LTS x86-64 (one machine).

    cd sim
    make help           # list of targets
    make check          # tool versions and source files
    make lint           # verilator --lint-only -Wall
    make TC1 WAVES=1    # run with +TEST1, writes TC1.log and waves.vcd
    make regress        # runs TC1 and TC2, prints REGRESSION PASSED/FAILED
    make covtxt         # merged coverage summary in cov_summary.txt
    make covhtml        # HTML line coverage in cov_html/index.html
    make clean
