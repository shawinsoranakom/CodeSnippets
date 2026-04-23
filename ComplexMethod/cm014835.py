def normalize_flash_attn_S(
        self,
        attn_unnorm,
        q,
        k,
        v,
        query_padding_mask=None,
        key_padding_mask=None,
        attn_bias=None,
        is_dropout=False,
        causal=False,
        window_size=(-1, -1),  # -1 means infinite window size
        scale=None,
    ):
        """
        Arguments:
            q: (batch_size, seqlen_q, nheads, head_dim)
            k, v: (batch_size, seqlen_k, nheads, head_dim)
            key_padding_mask: (batch_size, seqlen_q)
            attn_bias: broadcastable to (batch_size, nheads, seqlen_q, seqlen_k)
        Output:
            softmax_lse: (batch_size, nheads, seqlen_q)
            softmax_max: (batch_size, nheads, seqlen_q)
        """
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        if causal:
            window_size = (window_size[0], 0)
        q, k, v = q.float(), k.float(), v.float()
        _, seqlen_q, _, head_dim = q.shape
        seqlen_k = k.shape[1]
        b = q.shape[0]
        from torch.nn.attention.bias import _calculate_scale
        scale = _calculate_scale(head_dim, scale)
        scores = torch.matmul(q.transpose(1, 2) * scale, k.permute(0, 2, 3, 1))
        if key_padding_mask is not None:
            scores.masked_fill_(~key_padding_mask.view(b, 1, 1, -1), float("-inf"))
        if window_size[0] >= 0 or window_size[1] >= 0:
            local_mask = self.construct_local_mask(
                seqlen_q,
                seqlen_k,
                window_size,
                query_padding_mask,
                key_padding_mask,
                q.device,
            )
            scores.masked_fill_(local_mask, float("-inf"))
        if attn_bias is not None:
            scores = scores + attn_bias.to(dtype=scores.dtype)
        block_size_n = _get_block_size_n(scores.device, head_dim, is_dropout, causal)
        scores_block = scores.split(block_size_n, dim=-1)
        lse_block = torch.stack([torch.logsumexp(s, dim=-1) for s in scores_block], dim=-1)
        lse = torch.logsumexp(lse_block, dim=-1)
        # lse could be -inf (i.e. all values in scores are -inf), and we want to set those to inf
        # so that when we do torch.exp(m - lse), we get 0.0 instead of NaN.
        lse[lse == float("-inf")] = float("inf")
        scores_max_block = torch.stack([torch.amax(s, dim=-1) for s in scores_block], dim=-1)
        cummax_block = torch.cummax(scores_max_block.flip(-1), dim=-1).values.flip(-1).unbind(dim=-1)
        attn_unnorm_block = attn_unnorm.split(block_size_n, dim=-1)
        attn_norm = torch.cat(
            [
                a * (torch.exp(m - lse)).unsqueeze(-1)
                for a, m in zip(attn_unnorm_block, cummax_block)
            ],
            dim=-1,
        )
        if query_padding_mask is not None:
            attn_norm.masked_fill_(~query_padding_mask.view(b, 1, -1, 1), 0.0)
            # attn_norm.masked_fill_(rearrange(~query_padding_mask, "b s -> b 1 s 1"), 0.0)
        return attn_norm.to(dtype=attn_unnorm.dtype)