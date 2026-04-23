def forward(
        self,
        q_x: torch.Tensor,
        kv_x: torch.Tensor,
        biases: list[torch.Tensor] | None = None,
        use_memory_efficient_kernel: bool = False,
        use_lma: bool = False,
        lma_q_chunk_size: int = 1024,
        lma_kv_chunk_size: int = 4096,
        use_flash: bool = False,
        flash_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Args:
            q_x:
                [*, Q, C_q] query data
            kv_x:
                [*, K, C_k] key data
            biases:
                List of biases that broadcast to [*, H, Q, K]
            use_memory_efficient_kernel:
                Whether to use a custom memory-efficient attention kernel. This should be the default choice for most.
                If none of the "use_<...>" flags are True, a stock PyTorch implementation is used instead
            use_lma:
                Whether to use low-memory attention (Staats & Rabe 2021). If none of the "use_<...>" flags are True, a
                stock PyTorch implementation is used instead
            lma_q_chunk_size:
                Query chunk size (for LMA)
            lma_kv_chunk_size:
                Key/Value chunk size (for LMA)
        Returns
            [*, Q, C_q] attention update
        """
        if use_lma and (lma_q_chunk_size is None or lma_kv_chunk_size is None):
            raise ValueError("If use_lma is specified, lma_q_chunk_size and lma_kv_chunk_size must be provided")

        if use_flash and biases is not None:
            raise ValueError("use_flash is incompatible with the bias option. For masking, use flash_mask instead")

        attn_options = [use_memory_efficient_kernel, use_lma, use_flash]
        if sum(attn_options) > 1:
            raise ValueError("Choose at most one alternative attention algorithm")

        if biases is None:
            biases = []

        # [*, H, Q/K, C_hidden]
        query, key, value = self._prep_qkv(q_x, kv_x)
        key = permute_final_dims(key, (1, 0))

        # [*, H, Q, K]
        output = torch.matmul(query, key)
        for b in biases:
            output += b
        output = softmax_no_cast(output, -1)

        # [*, H, Q, C_hidden]
        output = torch.matmul(output, value)
        output = output.transpose(-2, -3)
        output = self._wrap_up(output, q_x)

        return output