def forward(self, input: Tensor, hx: Tensor | None = None) -> Tensor:
        if input.dim() not in (1, 2):
            raise AssertionError(
                f"RNNCell: Expected input to be 1-D or 2-D but received {input.dim()}-D tensor"
            )
        is_batched = input.dim() == 2
        if not is_batched:
            input = input.unsqueeze(0)

        if hx is None:
            hx = torch.zeros(
                input.size(0), self.hidden_size, dtype=input.dtype, device=input.device
            )
        else:
            hx = hx.unsqueeze(0) if not is_batched else hx

        if self.nonlinearity == "tanh":
            ret = _VF.rnn_tanh_cell(
                input,
                hx,
                self.get_weight_ih(),
                self.get_weight_hh(),
                self.bias_ih,
                self.bias_hh,
            )
        elif self.nonlinearity == "relu":
            ret = _VF.rnn_relu_cell(
                input,
                hx,
                self.get_weight_ih(),
                self.get_weight_hh(),
                self.bias_ih,
                self.bias_hh,
            )
        else:
            ret = input  # TODO: remove when jit supports exception flow
            raise RuntimeError(f"Unknown nonlinearity: {self.nonlinearity}")

        if not is_batched:
            ret = ret.squeeze(0)

        return ret