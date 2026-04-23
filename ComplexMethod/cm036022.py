def forward(ctx: Any,
                q: torch.Tensor, k: torch.Tensor, v: torch.Tensor,
                causal: bool, sm_scale: float) -> torch.Tensor:
        """
        ### Forward pass

        Group query attention forward pass. Returns the output in shape `[batch_size, n_heads, q_seq_len, d_head]`.

        :param ctx: is the context for torch gradient descent
        :param q: has shape `[batch_size, n_heads, q_seq_len, d_head]`
        :param q: has shape `[batch_size, n_heads, q_seq_len, d_head]`
        :param k: has shape `[batch_size, k_heads, kv_seq_len, d_head]`
        :param v: has shape `[batch_size, k_heads, kv_seq_len, d_head]`
        :param causal: whether to apply causal attention mask
        :param sm_scale: softmax scale factor $\sigma$
        """
        batch_size, n_heads, q_seq_len, d_head = q.shape
        _, k_heads, kv_seq_len, _ = k.shape
        assert n_heads % k_heads == 0
        n_groups = n_heads // k_heads

        # Shape constraints
        assert d_head == k.shape[-1] == v.shape[-1]
        assert d_head in {16, 32, 64, 128, 256}

        # Change the tensors combining the heads with the batch dimension
        q = q.view(batch_size * k_heads, n_groups, q_seq_len, d_head)
        k = k.view(batch_size * k_heads, kv_seq_len, d_head)
        v = v.view(batch_size * k_heads, kv_seq_len, d_head)

        # Make sure the tensors are contiguous and the strides are same
        assert q.is_contiguous()
        assert k.is_contiguous()
        assert v.is_contiguous()
        assert k.stride() == v.stride()

        # Tensor for the output
        o = torch.empty_like(q)
        # Tensor for log of sum of exponentials $\log_2 L_i = \log_2 \sum_j e^{S_{ij}}$
        lse = torch.empty((batch_size * k_heads, n_groups, q_seq_len), device=q.device, dtype=HI_PRES_TORCH)

        # The forward computation will be parallelized along the batch dimension and the queries in blocks of size `BLOCK_Q`
        grid = lambda meta: (triton.cdiv(q_seq_len, meta["BLOCK_Q"]), batch_size * k_heads * n_groups, 1)
        _attn_fwd[grid](
            q, k, v, sm_scale * 1.4426950408889634, lse, o,
            n_groups=n_groups,
            q_seq_len=q_seq_len,
            kv_seq_len=kv_seq_len,
            d_head=d_head,
            is_causal=causal,
        )

        # Save the reshaped inputs and outputs for the backward pass
        ctx.save_for_backward(q, k, v, o, lse)
        ctx.sm_scale = sm_scale
        ctx.n_groups = n_groups
        ctx.causal = causal

        # Return the output in shape `[batch_size, n_heads, q_seq_len, d_head]`
        return o.view(batch_size, n_heads, q_seq_len, d_head)