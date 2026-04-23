def forward(self, x: Tensor, hidden: tuple[Tensor, Tensor] | None = None):
        if self.batch_first:
            x = x.transpose(0, 1)

        max_batch_size = x.size(1)
        num_directions = 2 if self.bidirectional else 1
        if hidden is None:
            zeros = torch.zeros(
                num_directions,
                max_batch_size,
                self.hidden_size,
                dtype=torch.float,
                device=x.device,
            )
            zeros.squeeze_(0)
            if x.is_quantized:
                zeros = torch.quantize_per_tensor(
                    zeros, scale=1.0, zero_point=0, dtype=x.dtype
                )
            hxcx = [(zeros, zeros) for _ in range(self.num_layers)]
        else:
            hidden_non_opt = torch.jit._unwrap_optional(hidden)
            if isinstance(hidden_non_opt[0], Tensor):
                hx = hidden_non_opt[0].reshape(
                    self.num_layers, num_directions, max_batch_size, self.hidden_size
                )
                cx = hidden_non_opt[1].reshape(
                    self.num_layers, num_directions, max_batch_size, self.hidden_size
                )
                hxcx = [
                    (hx[idx].squeeze(0), cx[idx].squeeze(0))
                    for idx in range(self.num_layers)
                ]
            else:
                hxcx = hidden_non_opt

        hx_list = []
        cx_list = []
        for idx, layer in enumerate(self.layers):
            x, (h, c) = layer(x, hxcx[idx])
            hx_list.append(torch.jit._unwrap_optional(h))
            cx_list.append(torch.jit._unwrap_optional(c))
        hx_tensor = torch.stack(hx_list)
        cx_tensor = torch.stack(cx_list)

        # We are creating another dimension for bidirectional case
        # need to collapse it
        hx_tensor = hx_tensor.reshape(-1, hx_tensor.shape[-2], hx_tensor.shape[-1])
        cx_tensor = cx_tensor.reshape(-1, cx_tensor.shape[-2], cx_tensor.shape[-1])

        if self.batch_first:
            x = x.transpose(0, 1)

        return x, (hx_tensor, cx_tensor)