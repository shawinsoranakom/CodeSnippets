def update_ngram_gpu_tensors_incremental(
    input_batch: InputBatch,
    token_ids_gpu_tensor: torch.Tensor,
    num_tokens_no_spec_gpu: torch.Tensor,
    new_reqs: list[CachedRequestState],
    device: torch.device,
    _pinned_idx_buf: torch.Tensor,
    _pinned_val_buf: torch.Tensor,
) -> None:
    """Incrementally update token_ids_gpu_tensor and num_tokens_no_spec_gpu
    for ngram GPU proposer.
    """
    prev_req_id_to_index = input_batch.prev_req_id_to_index
    curr_req_id_to_index = input_batch.req_id_to_index

    if not curr_req_id_to_index:
        return

    active_indices = list(curr_req_id_to_index.values())
    n_active = len(active_indices)

    # Use resident pinned buffers to avoid per-call allocation.
    active_idx_cpu = _pinned_idx_buf[:n_active]
    active_idx_cpu.copy_(torch.as_tensor(active_indices, dtype=torch.long))

    active_idx_gpu = active_idx_cpu.to(device=device, non_blocking=True)

    new_req_ids = {req.req_id for req in new_reqs}

    # First run, no previous state.
    if prev_req_id_to_index is None:
        for idx in active_indices:
            num_tokens = input_batch.num_tokens_no_spec[idx]
            if num_tokens > 0:
                token_ids_gpu_tensor[idx, :num_tokens].copy_(
                    input_batch.token_ids_cpu_tensor[idx, :num_tokens],
                    non_blocking=True,
                )

        _sync_num_tokens(
            input_batch,
            num_tokens_no_spec_gpu,
            active_idx_cpu,
            active_idx_gpu,
            n_active,
            device,
            _pinned_val_buf,
        )
        return

    # Detect index changes for reorder.
    reorder_src: list[int] = []
    reorder_dst: list[int] = []

    for req_id, curr_idx in curr_req_id_to_index.items():
        if req_id in new_req_ids:
            continue
        prev_idx = prev_req_id_to_index.get(req_id)
        if prev_idx is not None and prev_idx != curr_idx:
            reorder_src.append(prev_idx)
            reorder_dst.append(curr_idx)

    if reorder_src:
        src_tensor = torch.tensor(reorder_src, dtype=torch.long, device=device)
        dst_tensor = torch.tensor(reorder_dst, dtype=torch.long, device=device)

        temp_token_ids = token_ids_gpu_tensor[src_tensor].clone()
        temp_num_tokens = num_tokens_no_spec_gpu[src_tensor].clone()

        token_ids_gpu_tensor[dst_tensor] = temp_token_ids
        num_tokens_no_spec_gpu[dst_tensor] = temp_num_tokens

    # Full copy for new/resumed requests.
    for req_state in new_reqs:
        new_req_idx = curr_req_id_to_index.get(req_state.req_id)
        if new_req_idx is None:
            continue

        num_tokens = input_batch.num_tokens_no_spec[new_req_idx]
        if num_tokens > 0:
            token_ids_gpu_tensor[new_req_idx, :num_tokens].copy_(
                input_batch.token_ids_cpu_tensor[new_req_idx, :num_tokens],
                non_blocking=True,
            )

    # Always batch-sync sequence lengths from CPU for ALL active requests.
    _sync_num_tokens(
        input_batch,
        num_tokens_no_spec_gpu,
        active_idx_cpu,
        active_idx_gpu,
        n_active,
        device,
        _pinned_val_buf,
    )