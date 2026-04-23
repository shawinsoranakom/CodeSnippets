def forward(self, x, causal: bool = True, timestep: Optional[torch.Tensor] = None):
        tid = threading.get_ident()
        cached, drop_first_conv, drop_first_res = self.temporal_cache_state.get(tid, (None, True, True))
        y = self.conv(x, causal=causal)
        y = rearrange(
            y,
            "b (c p1 p2 p3) d h w -> b c (d p1) (h p2) (w p3)",
            p1=self.stride[0],
            p2=self.stride[1],
            p3=self.stride[2],
        )
        if self.stride[0] == 2 and y.shape[2] > 0 and drop_first_conv:
            y = y[:, :, 1:, :, :]
            drop_first_conv = False
        if self.residual:
            # Reshape and duplicate the input to match the output shape
            x_in = rearrange(
                x,
                "b (c p1 p2 p3) d h w -> b c (d p1) (h p2) (w p3)",
                p1=self.stride[0],
                p2=self.stride[1],
                p3=self.stride[2],
            )
            num_repeat = math.prod(self.stride) // self.out_channels_reduction_factor
            x_in = x_in.repeat(1, num_repeat, 1, 1, 1)
            if self.stride[0] == 2 and x_in.shape[2] > 0 and drop_first_res:
                x_in = x_in[:, :, 1:, :, :]
                drop_first_res = False

            if y.shape[2] == 0:
                y = None

            cached = add_exchange_cache(y, cached, x_in, dim=2)
            self.temporal_cache_state[tid] = (cached, drop_first_conv, drop_first_res)

        else:
            self.temporal_cache_state[tid] = (None, drop_first_conv, False)

        return y