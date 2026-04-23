def forward(
        self, input: Tensor, hx: tuple[Tensor, Tensor] | None = None
    ) -> tuple[Tensor, Tensor]:
        if input.dim() not in (1, 2):
            raise ValueError(
                f"LSTMCell: Expected input to be 1D or 2D, got {input.dim()}D instead"
            )
        if hx is not None:
            for idx, value in enumerate(hx):
                if value.dim() not in (1, 2):
                    raise ValueError(
                        f"LSTMCell: Expected hx[{idx}] to be 1D or 2D, got {value.dim()}D instead"
                    )
        is_batched = input.dim() == 2
        if not is_batched:
            input = input.unsqueeze(0)

        if hx is None:
            zeros = torch.zeros(
                input.size(0), self.hidden_size, dtype=input.dtype, device=input.device
            )
            hx = (zeros, zeros)
        else:
            hx = (hx[0].unsqueeze(0), hx[1].unsqueeze(0)) if not is_batched else hx

        ret = _VF.lstm_cell(
            input,
            hx,
            self.weight_ih,
            self.weight_hh,
            self.bias_ih,
            self.bias_hh,
        )

        if not is_batched:
            ret = (ret[0].squeeze(0), ret[1].squeeze(0))
        return ret