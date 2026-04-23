def test_vocab_parallel_embedding_indices(tp_size, seed, default_vllm_config):
    random.seed(seed)
    vocab_size = random.randint(4000, 64000)
    added_vocab_size = random.randint(0, 1024)
    org_vocab_size = vocab_size - added_vocab_size
    last_org_vocab_end_index = 0
    last_added_vocab_end_index = org_vocab_size
    computed_vocab_size = 0
    computed_org_vocab_size = 0
    computed_added_vocab_size = 0
    vocab_size_padded = -1

    all_org_tokens: list[int] = []
    all_added_tokens: list[int] = []
    token_ids: list[int] = []

    for tp_rank in range(tp_size):
        with (
            patch(
                "vllm.model_executor.layers.vocab_parallel_embedding.get_tensor_model_parallel_rank",
                return_value=tp_rank,
            ),
            patch(
                "vllm.model_executor.layers.vocab_parallel_embedding.get_tensor_model_parallel_world_size",
                return_value=tp_size,
            ),
        ):
            vocab_embedding = VocabParallelEmbedding(
                vocab_size, 1, org_num_embeddings=org_vocab_size
            )
        vocab_size_padded = vocab_embedding.num_embeddings_padded
        shard_indices = vocab_embedding.shard_indices
        # Assert that the ranges are contiguous
        assert shard_indices.org_vocab_start_index == last_org_vocab_end_index
        assert shard_indices.added_vocab_start_index == last_added_vocab_end_index

        # Ensure that we are not exceeding the vocab size
        computed_vocab_size += shard_indices.num_elements_padded
        computed_org_vocab_size += shard_indices.num_org_elements
        computed_added_vocab_size += shard_indices.num_added_elements

        # Ensure that the ranges are not overlapping
        all_org_tokens.extend(
            range(
                shard_indices.org_vocab_start_index, shard_indices.org_vocab_end_index
            )
        )
        all_added_tokens.extend(
            range(
                shard_indices.added_vocab_start_index,
                shard_indices.added_vocab_end_index,
            )
        )

        token_ids.extend(
            range(
                shard_indices.org_vocab_start_index, shard_indices.org_vocab_end_index
            )
        )
        token_ids.extend(
            [-1]
            * (shard_indices.num_org_elements_padded - shard_indices.num_org_elements)
        )
        token_ids.extend(
            range(
                shard_indices.added_vocab_start_index,
                shard_indices.added_vocab_end_index,
            )
        )
        token_ids.extend(
            [-1]
            * (
                shard_indices.num_added_elements_padded
                - shard_indices.num_added_elements
            )
        )

        last_org_vocab_end_index = shard_indices.org_vocab_end_index
        last_added_vocab_end_index = shard_indices.added_vocab_end_index

    assert computed_vocab_size == vocab_size_padded
    assert computed_org_vocab_size == org_vocab_size
    assert computed_added_vocab_size == added_vocab_size

    # Ensure that the ranges are not overlapping
    assert len(all_org_tokens) == len(set(all_org_tokens))
    assert len(all_added_tokens) == len(set(all_added_tokens))
    assert not set(all_org_tokens).intersection(set(all_added_tokens))

    token_ids_tensor = torch.tensor(token_ids, dtype=torch.long)
    reindex_mapping = vocab_embedding.get_sharded_to_full_mapping()
    assert reindex_mapping is not None or tp_size == 1
    if reindex_mapping is not None:
        reindexed_token_ids = token_ids_tensor[reindex_mapping]
        expected = torch.tensor(list(range(0, vocab_size)))
        assert reindexed_token_ids[:vocab_size].equal(expected)
        assert torch.all(reindexed_token_ids[vocab_size:] == -1)