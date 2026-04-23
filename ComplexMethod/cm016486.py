def slice_cond(cond_value, window: IndexListContextWindow, x_in: torch.Tensor, device, temporal_dim: int, temporal_scale: int=1, temporal_offset: int=0, retain_index_list: list[int]=[]):
    if not (hasattr(cond_value, "cond") and isinstance(cond_value.cond, torch.Tensor)):
        return None
    cond_tensor = cond_value.cond
    if temporal_dim >= cond_tensor.ndim:
        return None

    cond_size = cond_tensor.size(temporal_dim)

    if temporal_scale == 1:
        expected_size = x_in.size(window.dim) - temporal_offset
        if cond_size != expected_size:
            return None

    if temporal_offset == 0 and temporal_scale == 1:
        sliced = window.get_tensor(cond_tensor, device, dim=temporal_dim, retain_index_list=retain_index_list)
        return cond_value._copy_with(sliced)

    # skip leading latent positions that have no corresponding conditioning (e.g. reference frames)
    if temporal_offset > 0:
        indices = [i - temporal_offset for i in window.index_list[temporal_offset:]]
        indices = [i for i in indices if 0 <= i]
    else:
        indices = list(window.index_list)

    if not indices:
        return None

    if temporal_scale > 1:
        scaled = []
        for i in indices:
            for k in range(temporal_scale):
                si = i * temporal_scale + k
                if si < cond_size:
                    scaled.append(si)
        indices = scaled
        if not indices:
            return None

    idx = tuple([slice(None)] * temporal_dim + [indices])
    sliced = cond_tensor[idx].to(device)
    return cond_value._copy_with(sliced)