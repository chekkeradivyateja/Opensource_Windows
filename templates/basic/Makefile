# =============================================================================
#  Simple Verilator Makefile: one RTL folder, one testbench folder, tests TC1, TC2, ...
#  WINDOWS version (MSYS2 UCRT64 terminal). Based on the Ubuntu 24.04 template.
#  Windows changes: C++ built with -O1 (GCC 16.2 -Os link error), CRLF fix before genhtml.
#  Start here:   make help
#  For bigger projects use makefile_templates/sv/Makefile or uvm/Makefile.
# =============================================================================
#  Layout:  <project>/rtl/*.sv   <project>/tb/*.sv   <project>/sim/Makefile (this file)
#  Test TCn runs the simulator with the plusarg +TESTn; the testbench selects the test
#  with $test$plusargs("TEST1"), $test$plusargs("TEST2"), ...
#  WAVES=1 compiles with -DDUMP_WAVES; the testbench needs an `ifdef DUMP_WAVES block
#  that calls $dumpfile("waves.vcd") and $dumpvars (see examples/counter/tb/tb_top.sv).
# =============================================================================

# ============================== EDIT HERE ====================================
# 1. Top testbench module
TOP    ?= tb_top
# 2. Design and testbench files (packages must come before the files that import them)
RTL    ?= $(wildcard ../rtl/*.sv ../rtl/*.v)
TB     ?= $(wildcard ../tb/*.sv)
# 3. Tests run by 'make regress' (TCn -> plusarg +TESTn)
TESTS  ?= TC1 TC2
# 4. Top design module (used by 'make synth')
RTL_TOP ?= counter
# =============================================================================
WAVES  ?= 0

VFLAGS := --binary --assert --coverage --trace -Wno-fatal --top-module $(TOP)
# Windows: the default -Os fails to link with MSYS2 GCC 16.2.0, so build the C++ with -O1
VFLAGS += -MAKEFLAGS "OPT_FAST=-O1 OPT_SLOW=-O1 OPT_GLOBAL=-O1"
ifeq ($(WAVES),1)
VFLAGS += -DDUMP_WAVES
endif

.PHONY: help check lint build regress covtxt covhtml synth clean

help:
	@echo "Targets:"
	@echo "  make check          show tool versions and the source files found"
	@echo "  make lint           verilator --lint-only -Wall on all files"
	@echo "  make build          compile into obj_dir/"
	@echo "  make TC1            run test 1 (plusarg +TEST1) -> TC1.log, TC1_cov.dat"
	@echo "  make TC1 WAVES=1    same, and write waves.vcd"
	@echo "  make regress        run all tests in TESTS, print REGRESSION PASSED/FAILED"
	@echo "  make covtxt         merged coverage summary -> cov_summary.txt, cov_annot/"
	@echo "  make covhtml        HTML line-coverage report -> cov_html/index.html"
	@echo "  make synth          Yosys synthesis of RTL_TOP -> synth.log, synth_stat.txt"
	@echo "  make clean          delete only generated files (obj_dir, TC*.log, TC*_cov.dat, cov_*, waves.vcd)"
	@echo "Current settings: TOP=$(TOP) TESTS=\"$(TESTS)\""

check:
	@verilator --version
	@command -v verilator_coverage >/dev/null && echo "verilator_coverage: found" || echo "verilator_coverage: MISSING"
	@command -v genhtml >/dev/null && echo "genhtml (lcov): found" || echo "genhtml (lcov): MISSING (needed for covhtml)"
	@echo "RTL files: $(RTL)"
	@echo "TB files:  $(TB)"

lint:
	verilator --lint-only -Wall --timing --top-module $(TOP) $(RTL) $(TB)

build:
	verilator $(VFLAGS) $(RTL) $(TB)

# TCn runs the simulation with plusarg +TESTn and keeps its coverage file
TC%: build
	./obj_dir/V$(TOP) +TEST$* 2>&1 | tee TC$*.log
	mv coverage.dat TC$*_cov.dat

regress:
	@for t in $(TESTS); do $(MAKE) --no-print-directory $$t || { echo "REGRESSION FAILED ($$t)"; exit 1; }; done
	@if grep -l -E '%Error|Assertion failed' $(addsuffix .log,$(TESTS)); \
	  then echo "REGRESSION FAILED"; exit 1; else echo "REGRESSION PASSED"; fi

covtxt:
	verilator_coverage --write coverage.dat *_cov.dat
	verilator_coverage --annotate cov_annot coverage.dat | tee cov_summary.txt

covhtml: covtxt
	verilator_coverage --write-info coverage.info coverage.dat
	sed -i 's/\r$$//' coverage.info
	genhtml coverage.info --output-directory cov_html

synth:
	yosys -q -l synth.log -p "read_verilog -sv $(RTL); synth -top $(RTL_TOP); tee -o synth_stat.txt stat"
	@cat synth_stat.txt

# Deletes only files this Makefile creates. Your own *.dat/*.hex/*.log files are kept.
clean:
	rm -rf obj_dir cov_annot cov_html
	rm -f TC*.log TC*_cov.dat coverage.dat coverage.info cov_summary.txt waves.vcd synth.log synth_stat.txt
