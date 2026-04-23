def _triton_convert_reference_impl(
    req_ids: torch.Tensor,
    block_table: torch.Tensor,
    token_indices: torch.Tensor,
    block_size: int,
    num_topk_tokens: int,
    HAS_PREFILL_WORKSPACE: bool = False,
    prefill_workspace_request_ids: torch.Tensor | None = None,
    prefill_workspace_starts: torch.Tensor | None = None,
) -> torch.Tensor:
    """Reference implementation for triton_convert_req_index_to_global_index."""
    num_tokens = req_ids.shape[0]
    max_blocks_per_req = block_table.shape[1]
    result = torch.empty(
        num_tokens, num_topk_tokens, dtype=torch.int32, device=req_ids.device
    )

    for token_id in range(num_tokens):
        req_id = req_ids[token_id].item()

        # Determine if this token uses workspace or paged cache
        use_prefill_workspace = False
        workspace_start = 0
        if HAS_PREFILL_WORKSPACE and prefill_workspace_request_ids is not None:
            assert prefill_workspace_starts is not None
            prefill_req_id = prefill_workspace_request_ids[token_id].item()
            if prefill_req_id >= 0:
                use_prefill_workspace = True
                workspace_start = prefill_workspace_starts[prefill_req_id].item()

        for idx_id in range(num_topk_tokens):
            token_idx = token_indices[token_id, idx_id].item()

            if token_idx == -1:
                result[token_id, idx_id] = -1
            elif use_prefill_workspace:
                # Prefill + using prefill workspace: map to workspace offset
                result[token_id, idx_id] = workspace_start + token_idx
            else:
                # Decode: map to paged cache
                block_id = token_idx // block_size
                if block_id >= max_blocks_per_req:
                    result[token_id, idx_id] = -1
                else:
                    block_num = block_table[req_id, block_id].item()
                    offset = token_idx % block_size
                    result[token_id, idx_id] = block_num * block_size + offset

    return result