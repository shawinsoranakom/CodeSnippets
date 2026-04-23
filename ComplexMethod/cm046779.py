def resolve_requested_gpu_ids(gpu_ids: Optional[list[int]]) -> list[int]:
    parent_visible_spec = _get_parent_visible_gpu_spec()
    parent_visible_ids = get_parent_visible_gpu_ids()
    physical_gpu_count = get_physical_gpu_count()

    if gpu_ids is None:
        return parent_visible_ids

    requested_ids = list(gpu_ids)
    if len(requested_ids) == 0:
        return parent_visible_ids

    if not parent_visible_spec["supports_explicit_gpu_ids"]:
        raise ValueError(
            f"Invalid gpu_ids {requested_ids}: explicit physical GPU IDs are "
            f"unsupported when CUDA_VISIBLE_DEVICES uses UUID/MIG entries "
            f"({parent_visible_spec['raw']!r}). Omit gpu_ids to use the "
            "parent-visible devices."
        )

    if len(set(requested_ids)) != len(requested_ids):
        raise ValueError(
            f"Invalid gpu_ids {requested_ids}: duplicate GPU IDs are not allowed. "
            f"Parent-visible GPUs: {parent_visible_ids}"
        )

    # Reject negative IDs unconditionally.
    negative_ids = [gpu_id for gpu_id in requested_ids if gpu_id < 0]
    if negative_ids:
        raise ValueError(
            f"Invalid gpu_ids {requested_ids}: GPU IDs must be non-negative. "
            f"Rejected IDs: {negative_ids}. Parent-visible GPUs: {parent_visible_ids}"
        )

    # Only enforce the physical upper bound when we have a reliable count
    # from nvidia-smi. When the count comes from torch, it reflects visible
    # devices (filtered by CUDA_VISIBLE_DEVICES), not the physical total,
    # so high physical indices like 3 would be falsely rejected on a
    # CUDA_VISIBLE_DEVICES="2,3" machine that reports device_count()=2.
    # The parent-visible check below is authoritative in all cases.
    if physical_gpu_count > 0 and parent_visible_ids:
        max_parent_id = max(parent_visible_ids)
        if physical_gpu_count > max_parent_id:
            # Count is plausibly physical (not just visible), so enforce it
            out_of_range = [
                gpu_id for gpu_id in requested_ids if gpu_id >= physical_gpu_count
            ]
            if out_of_range:
                raise ValueError(
                    f"Invalid gpu_ids {requested_ids}: IDs must be physical GPU IDs "
                    f"between 0 and {physical_gpu_count - 1}. "
                    f"Rejected IDs: {out_of_range}. Parent-visible GPUs: {parent_visible_ids}"
                )

    disallowed_ids = [
        gpu_id for gpu_id in requested_ids if gpu_id not in parent_visible_ids
    ]
    if disallowed_ids:
        raise ValueError(
            f"Invalid gpu_ids {requested_ids}: requested GPUs {disallowed_ids} are "
            f"outside the parent-visible set {parent_visible_ids}"
        )

    return requested_ids