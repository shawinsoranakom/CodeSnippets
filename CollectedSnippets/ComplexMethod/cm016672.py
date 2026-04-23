def forward(self, x, causal: bool = True):
        tid = threading.get_ident()

        cached, is_end = self.temporal_cache_state.get(tid, (None, False))
        if cached is None:
            padding_length = self.time_kernel_size - 1
            if not causal:
                padding_length = padding_length // 2
            if x.shape[2] == 0:
                return x
            cached = x[:, :, :1, :, :].repeat((1, 1, padding_length, 1, 1))
        pieces = [ cached, x ]
        if is_end and not causal:
            pieces.append(x[:, :, -1:, :, :].repeat((1, 1, (self.time_kernel_size - 1) // 2, 1, 1)))
        input_length = sum([piece.shape[2] for piece in pieces])
        cache_length = (self.time_kernel_size - self.time_stride) + ((input_length - self.time_kernel_size) % self.time_stride)

        needs_caching = not is_end
        if needs_caching and cache_length == 0:
            self.temporal_cache_state[tid] = (x[:, :, :0, :, :], False)
            needs_caching = False
        if needs_caching and x.shape[2] >= cache_length:
            needs_caching = False
            self.temporal_cache_state[tid] = (x[:, :, -cache_length:, :, :], False)

        x = torch.cat(pieces, dim=2)
        del pieces
        del cached

        if needs_caching:
            self.temporal_cache_state[tid] = (x[:, :, -cache_length:, :, :], False)
        elif is_end:
            self.temporal_cache_state[tid] = (None, True)

        return self.conv(x) if x.shape[2] >= self.time_kernel_size else x[:, :, :0, :, :]