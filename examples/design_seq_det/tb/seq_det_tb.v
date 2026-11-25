`timescale 1ns/1ps
module seq_det_tb;
  reg clk = 0, rst_n = 0, din = 0;
  wire dout;
  integer errors = 0, checks = 0, i;
  reg [3:0]  hist;                          // reference model: last 4 sampled bits
  reg        exp;
  reg [15:0] pattern = 16'b1011_0110_1101_1011;

  seq_det dut (.clk(clk), .rst_n(rst_n), .din(din), .dout(dout));
  always #5 clk = ~clk;

  always @(posedge clk or negedge rst_n)
    if (!rst_n) hist <= 4'b0000; else hist <= {hist[2:0], din};

  // dout must be 1 exactly in the cycle after the last 4 sampled bits were 1011
  always @(negedge clk) if (rst_n) begin
    checks = checks + 1;
    exp = (hist == 4'b1011);
    if (dout !== exp) begin
      errors = errors + 1;
      if (errors <= 5) $display("ERROR t=%0t hist=%b dout=%b expected=%b", $time, hist, dout, exp);
    end
  end

  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, seq_det_tb);
    #12 rst_n = 1;
    for (i = 15; i >= 0; i = i - 1) @(negedge clk) din = pattern[i];
    for (i = 0; i < 1000; i = i + 1) @(negedge clk) din = $random;
    @(negedge clk);
    $display("checks=%0d errors=%0d", checks, errors);
    if (errors == 0 && checks > 0) $display("PASS: all checks passed");
    else                           $display("FAIL: %0d errors", errors);
    $finish;
  end
endmodule
