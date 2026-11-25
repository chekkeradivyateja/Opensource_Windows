// alu.sv - 8-bit ALU with one-cycle registered output (example design)
// op: 0 = ADD, 1 = SUB, 2 = AND, 3 = XOR
`timescale 1ns/1ps
module alu (
  input  logic       clk,
  input  logic       rst_n,      // active-low synchronous reset
  input  logic       in_valid,
  input  logic [1:0] op,
  input  logic [7:0] a,
  input  logic [7:0] b,
  output logic       out_valid,
  output logic [8:0] result      // 9 bits: carry/borrow in bit 8
);
  always_ff @(posedge clk) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      result    <= '0;
    end else begin
      out_valid <= in_valid;
      if (in_valid) begin
        case (op)
          2'd0: result <= {1'b0, a} + {1'b0, b};
          2'd1: result <= {1'b0, a} - {1'b0, b};
          2'd2: result <= {1'b0, a & b};
          2'd3: result <= {1'b0, a ^ b};
        endcase
      end
    end
  end
endmodule
