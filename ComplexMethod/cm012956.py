def forward(self, x: Tensor, hidden: tuple[Tensor, Tensor] | None = None):
        if self.batch_first:
            x = x.transpose(0, 1)
        if hidden is None:
            hx_fw, cx_fw = (None, None)
        else:
            hx_fw, cx_fw = hidden
        hidden_bw: tuple[Tensor, Tensor] | None = None
        if self.bidirectional:
            if hx_fw is None:
                hx_bw = None
            else:
                hx_bw = hx_fw[1]
                hx_fw = hx_fw[0]
            if cx_fw is None:
                cx_bw = None
            else:
                cx_bw = cx_fw[1]
                cx_fw = cx_fw[0]
            if hx_bw is not None and cx_bw is not None:
                hidden_bw = hx_bw, cx_bw
        if hx_fw is None and cx_fw is None:
            hidden_fw = None
        else:
            hidden_fw = (
                torch.jit._unwrap_optional(hx_fw),
                torch.jit._unwrap_optional(cx_fw),
            )
        result_fw, hidden_fw = self.layer_fw(x, hidden_fw)

        if hasattr(self, "layer_bw") and self.bidirectional:
            x_reversed = x.flip(0)
            result_bw, hidden_bw = self.layer_bw(x_reversed, hidden_bw)
            result_bw = result_bw.flip(0)

            result = torch.cat([result_fw, result_bw], result_fw.dim() - 1)
            if hidden_fw is None and hidden_bw is None:
                h = None
                c = None
            elif hidden_fw is None:
                (h, c) = torch.jit._unwrap_optional(hidden_bw)
            elif hidden_bw is None:
                (h, c) = torch.jit._unwrap_optional(hidden_fw)
            else:
                h = torch.stack([hidden_fw[0], hidden_bw[0]], 0)  # type: ignore[list-item]
                c = torch.stack([hidden_fw[1], hidden_bw[1]], 0)  # type: ignore[list-item]
        else:
            result = result_fw
            h, c = torch.jit._unwrap_optional(hidden_fw)  # type: ignore[assignment]

        if self.batch_first:
            result.transpose_(0, 1)

        return result, (h, c)