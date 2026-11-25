# uvm_project: UVM testbench

Same ALU as `sv_project`, verified with a UVM environment (`tb/alu_pkg.sv`: item,
sequences, driver, monitor, scoreboard, coverage subscriber, agent, env, tests) and the
Makefile from `makefile_templates/uvm/` (`sim/`). Tests: `alu_smoke_test`, `alu_random_test`.

    cd sim
    make help
    make build                         # first time about 3 minutes, about 3 GB RAM
    make regress                       # REGRESSION PASSED
    make cov                           # coverage summary (covergroup 100%)
    make run TEST=alu_random_test WAVES=1 VERBOSITY=UVM_LOW
    make waves TEST=alu_random_test    # Surfer

Explained step by step in `docs/USER_GUIDE.md` (section 8, 10).
