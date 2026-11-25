// alu_tb_pkg.sv - transaction class for the alu testbench (compiled before tb_top.sv)
package alu_tb_pkg;
  class alu_txn;
    rand bit [1:0] op;
    rand bit [7:0] a, b;
    constraint c_ops   { op dist {0 := 4, 1 := 3, 2 := 2, 3 := 1}; }
    constraint c_edges { a dist {0 := 1, 255 := 1, [1:254] :/ 8};
                         b dist {0 := 1, 255 := 1, [1:254] :/ 8}; }
  endclass
endpackage
