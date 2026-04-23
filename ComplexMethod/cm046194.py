def select_closest_cond_frames(frame_idx: int, cond_frame_outputs: dict[int, Any], max_cond_frame_num: int):
    """Select the closest conditioning frames to a given frame index.

    Args:
        frame_idx (int): Current frame index.
        cond_frame_outputs (dict[int, Any]): Dictionary of conditioning frame outputs keyed by frame indices.
        max_cond_frame_num (int): Maximum number of conditioning frames to select.

    Returns:
        selected_outputs (dict[int, Any]): Selected items from cond_frame_outputs.
        unselected_outputs (dict[int, Any]): Items not selected from cond_frame_outputs.

    Examples:
        >>> frame_idx = 5
        >>> cond_frame_outputs = {1: "a", 3: "b", 7: "c", 9: "d"}
        >>> max_cond_frame_num = 2
        >>> selected, unselected = select_closest_cond_frames(frame_idx, cond_frame_outputs, max_cond_frame_num)
        >>> print(selected)
        {3: 'b', 7: 'c'}
        >>> print(unselected)
        {1: 'a', 9: 'd'}
    """
    if max_cond_frame_num == -1 or len(cond_frame_outputs) <= max_cond_frame_num:
        selected_outputs = cond_frame_outputs
        unselected_outputs = {}
    else:
        assert max_cond_frame_num >= 2, "we should allow using 2+ conditioning frames"
        selected_outputs = {}

        # The closest conditioning frame before `frame_idx` (if any)
        idx_before = max((t for t in cond_frame_outputs if t < frame_idx), default=None)
        if idx_before is not None:
            selected_outputs[idx_before] = cond_frame_outputs[idx_before]

        # The closest conditioning frame after `frame_idx` (if any)
        idx_after = min((t for t in cond_frame_outputs if t >= frame_idx), default=None)
        if idx_after is not None:
            selected_outputs[idx_after] = cond_frame_outputs[idx_after]

        # Add other temporally closest conditioning frames until reaching a total
        # of `max_cond_frame_num` conditioning frames.
        num_remain = max_cond_frame_num - len(selected_outputs)
        inds_remain = sorted(
            (t for t in cond_frame_outputs if t not in selected_outputs),
            key=lambda x: abs(x - frame_idx),
        )[:num_remain]
        selected_outputs.update((t, cond_frame_outputs[t]) for t in inds_remain)
        unselected_outputs = {t: v for t, v in cond_frame_outputs.items() if t not in selected_outputs}

    return selected_outputs, unselected_outputs