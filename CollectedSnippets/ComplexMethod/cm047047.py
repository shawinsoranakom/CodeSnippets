def build_sdpa_packed_attention_mask(
    seq_info: Tuple[torch.Tensor, torch.Tensor, int],
    *,
    dtype: torch.dtype,
    device: torch.device,
    sliding_window: Optional[int] = None,
) -> torch.Tensor:
    seq_lengths, _, _ = seq_info

    params = (dtype, sliding_window)
    entry = _SDPA_MASK_CACHE.get(device)
    if (
        entry is not None
        and entry["seq_lengths"] is seq_lengths
        and entry["params"] == params
    ):
        return entry["mask"]

    total_tokens = int(seq_lengths.sum().item())
    mask = torch.full(
        (total_tokens, total_tokens),
        float("-inf"),
        dtype = dtype,
        device = device,
    )
    offset = 0
    for length in seq_lengths.tolist():
        length = int(length)
        if length <= 0:
            continue
        block = torch.zeros((length, length), dtype = dtype, device = device)
        upper = torch.triu(
            torch.ones((length, length), device = device), diagonal = 1
        ).bool()
        block = block.masked_fill(upper, float("-inf"))
        if (
            sliding_window is not None
            and sliding_window > 0
            and length > sliding_window
        ):
            idx = torch.arange(length, device = device)
            dist = idx.unsqueeze(1) - idx.unsqueeze(0)
            window_mask = dist >= sliding_window
            block = block.masked_fill(window_mask, float("-inf"))
        mask[offset : offset + length, offset : offset + length] = block
        offset += length

    result = mask.unsqueeze(0).unsqueeze(0)
    _SDPA_MASK_CACHE[device] = {
        "seq_lengths": seq_lengths,
        "params": params,
        "mask": result,
    }
    return result