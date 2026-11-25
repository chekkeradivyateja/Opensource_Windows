// Testbench for counter. +TEST1 runs past wrap-around; default runs a short count.
`timescale 1ns/1ps
module tb_top;
  logic       clk;
  logic       rst = 1;
  logic       en  = 0;
  logic [7:0] count;
  int         cycles;

  counter dut (.clk, .rst, .en, .count);

  initial clk = 0;
  always #5 clk = ~clk;

  // count must increase by one on every enabled cycle
  assert property (@(posedge clk) disable iff (rst) en |=> count == $past(count) + 8'd1)
    else $error("count did not increment");

`ifdef DUMP_WAVES
  initial begin
    $dumpfile("waves.vcd");
    $dumpvars(0, tb_top);
  end
`endif

  initial begin
    if ($test$plusargs("TEST1")) begin
      cycles = 300;
      $display("Running TEST1 for %0d cycles", cycles);
    end else begin
      cycles = 10;
      $display("Running default test for %0d cycles", cycles);
    end
    repeat (2) @(posedge clk);
    rst <= 0;
    en  <= 1;
    repeat (cycles) @(posedge clk);
    en  <= 0;
    @(posedge clk);
    if (count != 8'(cycles)) $error("count = %0d, expected %0d", count, 8'(cycles));
    else                     $display("PASS: count = %0d", count);
    $finish;
  end
endmodule
