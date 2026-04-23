def build_xformers_block_causal_mask(
    seq_info: Optional[Tuple[torch.Tensor, torch.Tensor, int]],
    *,
    sliding_window: Optional[int] = None,
    base_mask: Optional[Any] = None,
):
    if _XFormersBlockMask is None:
        return None
    if seq_info is not None:
        seq_lengths, _, _ = seq_info
        # Cache the mask to avoid repeated D2H sync across layers
        device = seq_lengths.device
        params = (sliding_window,)
        entry = _XFORMERS_BLOCK_MASK_CACHE.get(device)
        if (
            entry is not None
            and entry["seq_lengths"] is seq_lengths
            and entry["params"] == params
        ):
            return entry["mask"]

        lengths_tensor = seq_lengths.to("cpu", torch.int32)
        if lengths_tensor.numel() == 0:
            return None
        lengths = tuple(int(x) for x in lengths_tensor.tolist())
        mask = _get_cached_block_mask(lengths, sliding_window)

        _XFORMERS_BLOCK_MASK_CACHE[device] = {
            "seq_lengths": seq_lengths,
            "params": params,
            "mask": mask,
        }
    else:
        mask = base_mask

        if (
            sliding_window is not None
            and sliding_window > 0
            and mask is not None
            and hasattr(mask, "make_local_attention")
        ):
            mask = mask.make_local_attention(window_size = sliding_window)
    return mask