def test_propose(method, attn_backend, num_speculative_tokens, monkeypatch):
    if attn_backend == "TRITON_ATTN" and not current_platform.is_rocm():
        pytest.skip(
            "TRITON_ATTN does not support "
            "multi-token eagle spec decode on current platform"
        )

    if attn_backend == "TREE_ATTN":
        pytest.skip(
            "TREE_ATTN is tested separately in test_propose_tree"
            "because it requires special input mocking."
        )

    if attn_backend == "ROCM_AITER_FA" and current_platform.is_rocm():
        monkeypatch.setenv("VLLM_ROCM_USE_AITER", "1")

    # Use GPU device
    device = torch.device(DEVICE_TYPE)

    # Setup test parameters
    batch_size = 2
    seq_len_1 = 5
    seq_len_2 = 3
    total_tokens = seq_len_1 + seq_len_2
    vocab_size = 100
    seq_lens = [seq_len_1, seq_len_2]

    # Create proposer first so we can use its actual hidden_size
    proposer = _create_proposer(
        "eagle", num_speculative_tokens, attention_backend=attn_backend
    )
    # Get the hidden_size from the proposer to ensure consistency
    hidden_size = proposer.hidden_size

    # Helper to create deterministic logits that will produce specific tokens
    def create_deterministic_logits(token_ids):
        logits = torch.full((batch_size, vocab_size), -100.0, device=device)
        for i, token_id in enumerate(token_ids):
            logits[i, token_id] = 100.0
        return logits

    # We mock a model that returns deterministic logits
    # Sequence 1: 42, 43, 44, ...
    # Sequence 2: 60, 61, 62, ...
    base_token_ids = [42, 60]

    # Skip loading the model and replace it with a mock directly
    # Create the mock model with deterministic outputs
    model_mock = mock.MagicMock()

    # Setup for model forward calls
    forward_returns = []
    for i in range(num_speculative_tokens):
        if i == 0:
            # First call uses all tokens
            h_logits = torch.zeros(total_tokens, hidden_size, device=device)
            h_states = torch.zeros(total_tokens, hidden_size, device=device)
        else:
            # Subsequent calls use batch_size tokens
            h_logits = torch.zeros(batch_size, hidden_size, device=device)
            h_states = torch.zeros(batch_size, hidden_size, device=device)
        forward_returns.append((h_logits, h_states))

    # For single token case, we only need the first item;
    # for multi-token, we need the sequence
    if num_speculative_tokens == 1:
        model_mock.return_value = forward_returns[0]
    else:
        model_mock.side_effect = forward_returns

    # Setup for compute_logits calls
    logits_returns = []
    for i in range(num_speculative_tokens):
        # For each call, increment the base token IDs
        current_tokens = [base_id + i for base_id in base_token_ids]
        logits_returns.append(create_deterministic_logits(current_tokens))

    if num_speculative_tokens == 1:
        model_mock.compute_logits.return_value = logits_returns[0]
    else:
        model_mock.compute_logits.side_effect = logits_returns

    # Assign the mock to the proposer
    proposer.model = model_mock

    # Assign draft attn_layer_names since load_model is not invoked
    proposer._draft_attn_layer_names = {"layer.0"}

    # Create input tensors
    batch_spec = BatchSpec(
        seq_lens=seq_lens,
        query_lens=seq_lens,
    )

    common_attn_metadata = create_common_attn_metadata(
        batch_spec,
        block_size=BLOCK_SIZE,
        device=device,
    )

    target_token_ids = torch.randint(0, vocab_size, (total_tokens,), device=device)
    target_positions = torch.cat(
        [torch.arange(seq_len_1, device=device), torch.arange(seq_len_2, device=device)]
    )
    target_hidden_states = torch.randn(total_tokens, hidden_size, device=device)
    next_token_ids = torch.randint(
        0, vocab_size, (batch_size,), dtype=torch.int32, device=device
    )
    sampling_metadata = mock.MagicMock()

    if attn_backend == "FLASH_ATTN":
        attn_metadata_builder_cls, _ = try_get_attention_backend(
            AttentionBackendEnum.FLASH_ATTN
        )
    elif attn_backend == "TRITON_ATTN":
        attn_metadata_builder_cls, _ = try_get_attention_backend(
            AttentionBackendEnum.TRITON_ATTN
        )
    elif attn_backend == "TREE_ATTN":
        attn_metadata_builder_cls, _ = try_get_attention_backend(
            AttentionBackendEnum.TREE_ATTN
        )
    elif attn_backend == "ROCM_AITER_FA":
        attn_metadata_builder_cls, _ = try_get_attention_backend(
            AttentionBackendEnum.ROCM_AITER_FA
        )
    else:
        raise ValueError(f"Unsupported attention backend: {attn_backend}")

    attn_metadata_builder = attn_metadata_builder_cls(
        kv_cache_spec=create_standard_kv_cache_spec(proposer.vllm_config),
        layer_names=proposer._draft_attn_layer_names,
        vllm_config=proposer.vllm_config,
        device=device,
    )

    # Mock runner and draft_attn_groups for attention metadata building
    proposer.runner = mock.MagicMock()
    mock_attn_group = mock.MagicMock()
    mock_attn_group.get_metadata_builder.return_value = attn_metadata_builder
    mock_attn_group.layer_names = list(proposer._draft_attn_layer_names)
    mock_attn_group.kv_cache_spec = attn_metadata_builder.kv_cache_spec
    proposer.draft_attn_groups = [mock_attn_group]

    result = proposer.propose(
        target_token_ids=target_token_ids,
        target_positions=target_positions,
        target_hidden_states=target_hidden_states,
        next_token_ids=next_token_ids,
        token_indices_to_sample=None,
        common_attn_metadata=common_attn_metadata,
        sampling_metadata=sampling_metadata,
    )

    assert result.shape == (batch_size, num_speculative_tokens)

    # Create expected tokens based on our token pattern
    if num_speculative_tokens == 1:
        # Example for num_speculative_tokens=1:
        # [[42], [60]]
        expected_tokens = torch.tensor(
            [[base_token_ids[0]], [base_token_ids[1]]], device=device
        )
    else:
        # Example for num_speculative_tokens=3:
        # [[42, 43, 44], [60, 61, 62]]
        expected_tokens = torch.zeros(
            (batch_size, num_speculative_tokens), dtype=torch.int64, device=device
        )
        for i in range(batch_size):
            for j in range(num_speculative_tokens):
                expected_tokens[i, j] = base_token_ids[i] + j

    # Verify all tokens match our expectations
    assert torch.equal(result, expected_tokens)