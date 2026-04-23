def gather_kv_caches(
    kv_caches_ptrs: torch.Tensor,
    total_token_in_kvcache: int,
    dst_tensor: torch.Tensor,
    token_indices: list[int],
    is_mla: bool = False,
) -> None:
    """Gather KV cache data from KV cache storage to destination tensor.

    Args:
        kv_caches_ptrs: Tensor of KV cache pointers (one per layer)
        total_token_in_kvcache: Total number of tokens in KV cache
        dst_tensor: Destination tensor to store gathered data
            - MHA format: [num_layers, 2, num_tokens_in_block, hidden_size]
            - MLA format: [num_layers, num_tokens_in_block, hidden_size]
        token_indices: List of token positions to gather
        is_mla: Whether using MLA model format
    """
    num_layers = kv_caches_ptrs.shape[0]
    num_tokens_in_block = len(token_indices)

    if is_mla:
        # MLA: dst_tensor is [num_layers, num_tokens_in_block, hidden_size]
        assert len(dst_tensor.shape) == 3, (
            f"MLA dst_tensor should be 3D, got {dst_tensor.shape}"
        )
        assert dst_tensor.shape[0] == num_layers, (
            f"Layer count mismatch: {dst_tensor.shape[0]} vs {num_layers}"
        )
        assert dst_tensor.shape[1] == num_tokens_in_block, (
            f"Token count mismatch: {dst_tensor.shape[1]} vs {num_tokens_in_block}"
        )
        hidden_size = dst_tensor.shape[2]
    else:
        # MHA: dst_tensor is [num_layers, 2, num_tokens_in_block, hidden_size]
        assert len(dst_tensor.shape) == 4, (
            f"MHA dst_tensor should be 4D, got {dst_tensor.shape}"
        )
        assert dst_tensor.shape[0] == num_layers, (
            f"Layer count mismatch: {dst_tensor.shape[0]} vs {num_layers}"
        )
        assert dst_tensor.shape[1] == 2, (
            f"MHA should have 2 (K,V) components, got {dst_tensor.shape[1]}"
        )
        assert dst_tensor.shape[2] == num_tokens_in_block, (
            f"Token count mismatch: {dst_tensor.shape[2]} vs {num_tokens_in_block}"
        )
        hidden_size = dst_tensor.shape[3]

    device = dst_tensor.device
    token_indices_tensor = torch.tensor(
        token_indices, dtype=torch.int32, device="cpu"
    ).to(device, non_blocking=True)

    grid = (num_layers, num_tokens_in_block)
    BLOCK_SIZE = 128

    kv_cache_gather_kernel[grid](
        kv_caches_ptrs,
        dst_tensor,
        token_indices_tensor,
        num_tokens_in_block,
        hidden_size,
        total_token_in_kvcache,
        num_layers,
        is_mla,
        BLOCK_SIZE=BLOCK_SIZE,
    )