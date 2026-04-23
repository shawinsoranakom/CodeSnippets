def test_mm_prefix_caching():
    """
    This tests that the multi-modal prefix caching is correct.
    """

    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 11),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    # Common prompt tokens (T is text tokens and P is image placeholder tokens)
    # [T,...,T, P0,...,P0], [P0,...,P0,T,...,T,P1,...,P1], [P1,...,P1]
    common_token_ids = list(range(10)) + [-1] * 6
    common_token_ids += [-1] * 4 + list(range(10, 20)) + [-1] * 2
    common_token_ids += [-1] * 16

    common_mm_positions = [
        PlaceholderRange(offset=11, length=10),
        PlaceholderRange(offset=30, length=18),
    ]
    common_mm_hashes = ["aaa", "bbb"]

    # A unique image plus some text tokens.
    unique_token_ids = [-1] * 7 + [100] * 4
    all_token_ids = common_token_ids + unique_token_ids
    mm_positions = common_mm_positions + [PlaceholderRange(offset=48, length=7)]
    mm_hashes = common_mm_hashes + ["ccc"]
    req0 = make_request(
        "0",
        all_token_ids,
        block_size,
        sha256,
        mm_positions=mm_positions,
        mm_hashes=mm_hashes,
    )
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)

    # Completed block should have hashes
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    block_hashes = req0.block_hashes
    assert len(block_hashes) == 3
    assert block_hashes[0] == sha256(
        (
            kv_cache_utils.NONE_HASH,
            tuple(all_token_ids[:block_size]),
            (("aaa", 11),),
        )
    )
    assert block_hashes[1] == sha256(
        (
            block_hashes[0],
            tuple(all_token_ids[block_size : block_size * 2]),
            (("aaa", -5), ("bbb", 14)),
        )
    )
    assert block_hashes[2] == sha256(
        (
            block_hashes[1],
            tuple(all_token_ids[block_size * 2 : block_size * 3]),
            (("bbb", -2),),
        )
    )

    blocks = manager.allocate_slots(
        req0, 59, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None
    assert blocks.get_block_ids() == ([1, 2, 3, 4],)
    req0.num_computed_tokens = 59

    # Append slots without allocating a new block.
    for _ in range(5):
        req0.append_output_token_ids(8)
    new_blocks = manager.allocate_slots(
        req0, 5, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert new_blocks is not None and len(new_blocks.blocks[0]) == 0
    assert len(block_hashes) == 4
    assert block_hashes[3] == sha256(
        (
            block_hashes[2],
            tuple(all_token_ids[3 * block_size :] + [8] * 5),
            (("ccc", 0),),
        )
    )

    # Cache hit.
    unique_token_ids = [-1] * 7 + [200] * 5
    all_token_ids = common_token_ids + unique_token_ids
    mm_positions = common_mm_positions + [PlaceholderRange(offset=48, length=7)]
    mm_hashes = common_mm_hashes + ["ccc"]
    req1 = make_request(
        "1",
        all_token_ids,
        block_size,
        sha256,
        mm_positions=mm_positions,
        mm_hashes=mm_hashes,
    )
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert len(computed_blocks.blocks[0]) == 3
    assert num_computed_tokens == 3 * 16