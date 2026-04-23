def forward(self, x, causal: bool = True):
        tid = threading.get_ident()
        cached, pad_first, cached_x, cached_input = self.temporal_cache_state.get(tid, (None, True, None, None))
        if cached_input is not None:
            x = torch_cat_if_needed([cached_input, x], dim=2)
            cached_input = None

        if self.stride[0] == 2 and pad_first:
            x = torch.cat(
                [x[:, :, :1, :, :], x], dim=2
            )  # duplicate first frames for padding
            pad_first = False

        if x.shape[2] < self.stride[0]:
            cached_input = x
            self.temporal_cache_state[tid] = (cached, pad_first, cached_x, cached_input)
            return None

        # skip connection
        x_in = rearrange(
            x,
            "b c (d p1) (h p2) (w p3) -> b (c p1 p2 p3) d h w",
            p1=self.stride[0],
            p2=self.stride[1],
            p3=self.stride[2],
        )
        x_in = rearrange(x_in, "b (c g) d h w -> b c g d h w", g=self.group_size)
        x_in = x_in.mean(dim=2)

        # conv
        x = self.conv(x, causal=causal)
        if self.stride[0] == 2 and x.shape[2] == 1:
            if cached_x is not None:
                x = torch_cat_if_needed([cached_x, x], dim=2)
                cached_x = None
            else:
                cached_x = x
                x = None

        if x is not None:
            x = rearrange(
                x,
                "b c (d p1) (h p2) (w p3) -> b (c p1 p2 p3) d h w",
                p1=self.stride[0],
                p2=self.stride[1],
                p3=self.stride[2],
            )

        cached = add_exchange_cache(x, cached, x_in, dim=2)

        self.temporal_cache_state[tid] = (cached, pad_first, cached_x, cached_input)

        return x