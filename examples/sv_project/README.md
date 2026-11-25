# sv_project: SystemVerilog + SVA + functional coverage

8-bit ALU (`rtl/`), assertions attached with `bind` (`sva/`), constrained-random
testbench with a covergroup and a reference-model checker (`tb/`), and the Makefile
from `makefile_templates/sv/` (`sim/`). Tests: `smoke`, `random`.

    cd sim
    make help
    make lint
    make regress                       # REGRESSION PASSED
    make cov                           # coverage summary (covergroup 100%)
    make covhtml && make covopen       # HTML report in the browser
    make run TEST=random WAVES=1
    make waves TEST=random             # Surfer

Explained step by step in `docs/USER_GUIDE.md` (sections 2-7, 10).
