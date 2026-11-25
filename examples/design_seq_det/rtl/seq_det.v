// Moore sequence detector for "1011" (overlapping). Fresh training example.
module seq_det (
  input  wire clk,
  input  wire rst_n,   // asynchronous, active-low reset
  input  wire din,
  output reg  dout
);
  localparam [2:0] S0 = 3'd0, S1 = 3'd1, S10 = 3'd2, S101 = 3'd3, S1011 = 3'd4;
  reg [2:0] state, next;

  always @(posedge clk or negedge rst_n)
    if (!rst_n) state <= S0;
    else        state <= next;

  always @(*) begin
    case (state)
      S0:    next = din ? S1    : S0;
      S1:    next = din ? S1    : S10;
      S10:   next = din ? S101  : S0;
      S101:  next = din ? S1011 : S10;
      S1011: next = din ? S1    : S10;
      default: next = state;  // keeps Yosys FSM extraction working with an async reset
    endcase
  end

  always @(*) dout = (state == S1011);   // Moore output: depends on the state only
endmodule
