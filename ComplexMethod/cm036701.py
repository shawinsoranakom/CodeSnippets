def ref_paged_attn(
    query: torch.Tensor,
    key_cache: torch.Tensor,
    value_cache: torch.Tensor,
    query_lens: list[int],
    kv_lens: list[int],
    block_tables: torch.Tensor,
    scale: float,
    sliding_window: int | None = None,
    soft_cap: float | None = None,
    alibi_slopes: torch.Tensor | None = None,
    s_aux: torch.Tensor | None = None,
) -> torch.Tensor:
    num_seqs = len(query_lens)
    block_tables = block_tables.cpu().numpy()
    _, block_size, num_kv_heads, head_size = key_cache.shape
    dtype = query.dtype

    outputs: list[torch.Tensor] = []
    start_idx = 0

    if alibi_slopes is not None:
        alibi_slopes = alibi_slopes[:, None, None]

    if s_aux is not None:
        s_aux = s_aux.float()
        s_aux = s_aux[:, None, None]

    for i in range(num_seqs):
        query_len = query_lens[i]
        kv_len = kv_lens[i]
        q = query[start_idx : start_idx + query_len].float()
        q *= scale

        num_kv_blocks = (kv_len + block_size - 1) // block_size
        block_indices = block_tables[i, :num_kv_blocks]

        k = key_cache[block_indices].view(-1, num_kv_heads, head_size)
        k = k[:kv_len].float()
        v = value_cache[block_indices].view(-1, num_kv_heads, head_size)
        v = v[:kv_len].float()

        if q.shape[1] != k.shape[1]:
            k = torch.repeat_interleave(k, q.shape[1] // k.shape[1], dim=1)
            v = torch.repeat_interleave(v, q.shape[1] // v.shape[1], dim=1)
        attn = torch.einsum("qhd,khd->hqk", q, k).float()
        empty_mask = torch.ones(query_len, kv_len)
        mask = torch.triu(empty_mask, diagonal=kv_len - query_len + 1).bool()

        if sliding_window is not None:
            sliding_window_mask = (
                torch.triu(
                    empty_mask, diagonal=kv_len - (query_len + sliding_window) + 1
                )
                .bool()
                .logical_not()
            )
            mask |= sliding_window_mask

        if soft_cap is not None:
            attn = soft_cap * torch.tanh(attn / soft_cap)

        if alibi_slopes is not None:
            q_start_pos = kv_len - query_len
            q_pos = q_start_pos + torch.arange(0, query_len)[None, :, None]
            kv_pos = torch.arange(0, kv_len)[None, None, :]
            dist = q_pos - kv_pos
            alibi_bias = -alibi_slopes * dist
            attn += alibi_bias

        attn.masked_fill_(mask, float("-inf"))

        if s_aux is not None:
            s_aux_ext = s_aux.repeat(1, query_len, 1)
            attn = torch.cat((s_aux_ext, attn), dim=-1)

        attn = torch.softmax(attn, dim=-1)

        if s_aux is not None:
            attn = attn[:, :, 1:]

        out = torch.einsum("hqk,khd->qhd", attn, v).to(dtype=dtype)

        outputs.append(out)
        start_idx += query_len

    return torch.cat(outputs, dim=0)