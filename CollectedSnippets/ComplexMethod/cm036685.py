def test_swap_blocks(
    kv_cache_factory,
    direction: tuple[str, str],
    num_mappings: int,
    num_heads: int,
    head_size: int,
    block_size: int,
    num_blocks: int,
    dtype: torch.dtype,
    seed: int,
    device: str,
    kv_cache_dtype: str,
) -> None:
    if kv_cache_dtype == "fp8" and "cpu" in direction:
        pytest.skip()
    if kv_cache_dtype == "fp8" and head_size % 16:
        pytest.skip()

    set_random_seed(seed)

    src_device = device if direction[0] == "cuda" else "cpu"
    dst_device = device if direction[1] == "cuda" else "cpu"

    src_blocks = random.sample(range(num_blocks), num_mappings)
    # For the same device, mapping must not overlap
    if src_device == dst_device:
        remaining_blocks = list(set(range(num_blocks)) - set(src_blocks))
        dst_blocks = random.sample(remaining_blocks, num_mappings)
    else:
        dst_blocks = random.sample(range(num_blocks), num_mappings)

    block_mapping = list(zip(src_blocks, dst_blocks))
    block_mapping_tensor = torch.tensor(
        block_mapping, dtype=torch.int64, device="cpu"
    ).view(-1, 2)

    # Create the KV caches on the first device.
    src_key_caches, src_value_caches = kv_cache_factory(
        num_blocks,
        block_size,
        1,
        num_heads,
        head_size,
        kv_cache_dtype,
        dtype,
        seed,
        src_device,
    )

    # Create the KV caches on the second device.
    dist_key_caches, dist_value_caches = kv_cache_factory(
        num_blocks,
        block_size,
        1,
        num_heads,
        head_size,
        kv_cache_dtype,
        dtype,
        seed,
        dst_device,
    )

    src_key_caches_clone = src_key_caches[0].clone()
    src_value_caches_clone = src_value_caches[0].clone()

    # Call the swap_blocks kernel.
    do_opcheck = head_size == HEAD_SIZES[0]
    src_cache = src_key_caches[0]
    block_size_in_bytes = src_cache.element_size() * src_cache.stride(0)
    opcheck(
        torch.ops._C_cache_ops.swap_blocks,
        (
            src_key_caches[0],
            dist_key_caches[0],
            block_size_in_bytes,
            block_mapping_tensor,
        ),
        cond=do_opcheck,
    )
    opcheck(
        torch.ops._C_cache_ops.swap_blocks,
        (
            src_value_caches[0],
            dist_value_caches[0],
            block_size_in_bytes,
            block_mapping_tensor,
        ),
        cond=do_opcheck,
    )

    ops.swap_blocks(
        src_key_caches[0],
        dist_key_caches[0],
        block_size_in_bytes,
        block_mapping_tensor,
    )
    ops.swap_blocks(
        src_value_caches[0],
        dist_value_caches[0],
        block_size_in_bytes,
        block_mapping_tensor,
    )

    for src, dst in block_mapping:
        torch.testing.assert_close(
            src_key_caches_clone[src].cpu(), dist_key_caches[0][dst].cpu()
        )
        torch.testing.assert_close(
            src_value_caches_clone[src].cpu(), dist_value_caches[0][dst].cpu()
        )