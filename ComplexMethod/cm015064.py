def forward_sdpa(
        self,
        x_padded: torch.Tensor,
        seq_lengths: torch.Tensor,
        scale: float | None = None,
        window_size: tuple[int, int] = (-1, -1),
    ):
        batch_size, seq_len, _ = x_padded.shape

        q = self.q_proj(x_padded)
        kv = self.kv_proj(x_padded)
        k, v = kv.view(batch_size, seq_len, 2, self.num_kv_heads, self.head_dim).unbind(
            dim=2
        )

        padding_mask = (
            torch.arange(seq_len, device=x_padded.device)[None, :]
            < seq_lengths[:, None]
        )

        attn_mask = padding_mask[:, None, None, :].expand(
            batch_size, self.num_heads, seq_len, seq_len
        )

        if window_size == (-1, 0):
            causal_mask = torch.tril(
                torch.ones(seq_len, seq_len, device=x_padded.device, dtype=torch.bool)
            )
            # Combine: attention allowed where BOTH padding is valid AND causal constraint is met
            attn_mask = attn_mask & causal_mask[None, None, :, :]

        if window_size[0] >= 0 or window_size[1] >= 0:
            window_mask = torch.zeros(
                seq_len, seq_len, dtype=torch.bool, device=x_padded.device
            )
            for i in range(seq_len):
                start = i - window_size[0] if window_size[0] >= 0 else 0
                end = i + window_size[1] + 1 if window_size[1] >= 0 else seq_len
                start = max(start, 0)
                end = min(end, seq_len)
                window_mask[i, start:end] = True
            attn_mask = attn_mask & window_mask[None, None, :, :]

        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(
            1, 2
        )
        v = v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(
            1, 2
        )

        # Don't pass is_causal since we already incorporated it into attn_mask.
        if self.enable_gqa:
            # Force math backend for GQA
            with torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.MATH):
                attn_out = F.scaled_dot_product_attention(
                    q,
                    k,
                    v,
                    attn_mask=attn_mask,
                    scale=scale,
                    enable_gqa=True,
                )
        else:
            attn_out = F.scaled_dot_product_attention(
                q,
                k,
                v,
                attn_mask=attn_mask,
                scale=scale,
            )

        attn_out = (
            attn_out.transpose(1, 2)
            .contiguous()
            .view(batch_size, seq_len, self.embed_dim)
        )

        return self.out_proj(attn_out)