def test_tree_attn_correctness(
    reference_backend: AttentionBackendEnum,
) -> None:
    set_random_seed(42)

    device = "cuda"
    tree_attn_masks = {
        # Chain.
        "[(0,), (0, 0), (0, 0, 0)]": torch.tensor(
            [
                [1, 0, 0, 0],
                [1, 1, 0, 0],
                [1, 1, 1, 0],
                [1, 1, 1, 1],
            ],
            device=device,
            dtype=torch.int32,
        ),
        # Tree.
        "[(0,), (1,), (0, 0), (0, 1), (1, 0), (1, 1)]": torch.tensor(
            [
                [1, 0, 0, 0, 0, 0, 0],
                [1, 1, 0, 0, 0, 0, 0],
                [1, 0, 1, 0, 0, 0, 0],
                [1, 1, 0, 1, 0, 0, 0],
                [1, 1, 0, 0, 1, 0, 0],
                [1, 0, 1, 0, 0, 1, 0],
                [1, 0, 1, 0, 0, 0, 1],
            ],
            device=device,
            dtype=torch.int32,
        ),
    }

    dim_per_head = 128
    num_kv_heads = 2
    block_size = 32
    max_sequence_length = 8192
    randomize_blocks = True
    for batch_size in [1, 16, 32]:
        for num_heads in [2, 4]:
            for sequence_position in [16, 1024, 2048]:
                for spec_token_tree, tree_attn_mask in tree_attn_masks.items():
                    # Assert that the number of heads is divisible
                    # by the number of KV heads.
                    assert num_heads % num_kv_heads == 0

                    # Initialize q, k, and v.
                    tree_size_q = tree_attn_mask.shape[0]
                    seqlen_k = sequence_position + tree_size_q
                    q = torch.randn(
                        (batch_size, tree_size_q, num_heads, dim_per_head),
                        device=device,
                        dtype=torch.bfloat16,
                    )
                    k = torch.randn(
                        (batch_size, tree_size_q, num_kv_heads, dim_per_head),
                        device=device,
                        dtype=torch.bfloat16,
                    )
                    v = torch.randn(
                        (batch_size, tree_size_q, num_kv_heads, dim_per_head),
                        device=device,
                        dtype=torch.bfloat16,
                    )

                    # KV cache in flash layout - the canonical format for
                    # tree attention. forward_attention() handles conversion
                    # when needed.
                    assert max_sequence_length % block_size == 0
                    max_blocks_per_batch = max_sequence_length // block_size
                    kv_cache = torch.randn(
                        (
                            2,
                            batch_size * max_blocks_per_batch,
                            block_size,
                            num_kv_heads,
                            dim_per_head,
                        ),
                        device=q.device,
                        dtype=torch.bfloat16,
                    )
                    num_alloc_blocks_per_batch = math.ceil(seqlen_k / block_size)
                    block_table = torch.zeros(
                        (batch_size, max_blocks_per_batch),
                        device=q.device,
                        dtype=torch.int32,
                    )
                    block_ids = torch.arange(
                        0,
                        batch_size * num_alloc_blocks_per_batch,
                        device=q.device,
                        dtype=torch.int32,
                    )
                    if randomize_blocks:
                        # Randomize the block ids.
                        block_ids = block_ids[torch.randperm(block_ids.numel())]
                    block_table[:, :num_alloc_blocks_per_batch] = block_ids.view(
                        -1, num_alloc_blocks_per_batch
                    )

                    # Set up the slot mapping for the input KVs.
                    tree_positions = sequence_position + torch.arange(
                        0,
                        tree_size_q,
                        device=q.device,
                        dtype=torch.int64,
                    ).repeat(batch_size, 1)
                    tree_slot_mapping = _gen_slot_mapping(
                        tree_positions, block_table, block_size
                    )

                    # Compute attention for the tree.
                    tree_attn_output = forward_attention(
                        q=q,
                        k=k,
                        v=v,
                        kv_cache=kv_cache,
                        block_table=block_table,
                        slot_mapping=tree_slot_mapping,
                        seqlen_k=seqlen_k,
                        backend=AttentionBackendEnum.TREE_ATTN,
                        spec_token_tree=spec_token_tree,
                        num_spec_tokens=tree_size_q - 1,
                    ).view(batch_size, -1, num_heads, dim_per_head)

                    # Verify each branch against the reference backend.
                    for q_index in range(tree_size_q):
                        # Get the q, k, and v for the branch.
                        branch_mask = tree_attn_mask[q_index, :]
                        branch_indices = torch.nonzero(branch_mask, as_tuple=True)[0]
                        q_len = branch_indices.shape[0]
                        q_branch = q[:, branch_indices]
                        k_branch = k[:, branch_indices]
                        v_branch = v[:, branch_indices]

                        # Setup slot mapping for the branch.
                        branch_positions = sequence_position + torch.arange(
                            0,
                            q_len,
                            device=q.device,
                            dtype=torch.int64,
                        ).repeat(batch_size, 1)
                        branch_slot_mapping = _gen_slot_mapping(
                            branch_positions, block_table, block_size
                        )

                        # Reference attention for this branch.
                        ref_output = forward_attention(
                            q=q_branch,
                            k=k_branch,
                            v=v_branch,
                            kv_cache=kv_cache,
                            block_table=block_table,
                            slot_mapping=branch_slot_mapping,
                            seqlen_k=sequence_position + q_len,
                            backend=reference_backend,
                        ).view(batch_size, -1, num_heads, dim_per_head)

                        # Compare the outputs.
                        assert torch.allclose(
                            tree_attn_output[:, branch_indices],
                            ref_output,
                            atol=7.81e-3,
                        ), (
                            f"outputs are not close for "
                            f"reference_backend: {reference_backend.name}, "
                            f"batch_size: {batch_size}, "
                            f"num_heads: {num_heads}, "
                            f"sequence_position: {sequence_position}, "
                            f"tree_attn_mask: {tree_attn_mask}, "
                            f"q_index: {q_index}."
                        )