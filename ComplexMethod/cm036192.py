def test_load_model(
    mock_get_model,
    mock_get_layers,
    mock_get_pp_group,
    method,
    attn_backend,
    pp_size,
    use_distinct_embed_tokens,
    use_distinct_lm_head,
    monkeypatch,
):
    if attn_backend == "ROCM_AITER_FA" and current_platform.is_rocm():
        monkeypatch.setenv("VLLM_ROCM_USE_AITER", "1")

    # Setup draft model mock
    mock_model = mock.MagicMock()
    mock_model.model = mock.MagicMock()
    mock_model.has_own_embed_tokens = use_distinct_embed_tokens
    if use_distinct_embed_tokens:
        mock_model.model.embed_tokens = mock.MagicMock()
    mock_model.has_own_lm_head = use_distinct_lm_head
    if use_distinct_lm_head:
        mock_model.lm_head = mock.MagicMock()

    mock_get_model.return_value = mock_model

    # Setup mocks for attention layers
    target_attn_layers = {
        "target_attn_1": mock.MagicMock(),
        "target_attn_2": mock.MagicMock(),
    }
    target_indx_layers: dict[str, mock.MagicMock] = {}
    # Draft model has one extra attention layer compared to target model
    all_attn_layers = {**target_attn_layers, "draft_extra_attn": mock.MagicMock()}

    all_indx_layers: dict[str, mock.MagicMock] = {}

    # Make mock_get_layers return different values for each call
    mock_get_layers.side_effect = [
        target_attn_layers,
        target_indx_layers,
        all_attn_layers,
        all_indx_layers,
    ]

    # Setup mock for pp group to return the appropriate value for world size
    mock_pp_group = mock.MagicMock()
    mock_pp_group.world_size = pp_size
    mock_get_pp_group.return_value = mock_pp_group

    # Set up the target model mock with a custom class so that
    # isinstance() checks match the expected type.
    class _TargetModelStub(LlamaForCausalLM):
        model: mock.MagicMock
        lm_head: mock.MagicMock

    target_model = mock.create_autospec(_TargetModelStub, instance=True)
    target_model.model = mock.MagicMock()
    target_model.lm_head = mock.MagicMock()
    target_model.model.embed_tokens = mock.MagicMock()

    from vllm.model_executor.models import SupportsMultiModal

    assert not isinstance(target_model, SupportsMultiModal)

    # Create proposer using the helper function
    proposer = _create_proposer(
        method, num_speculative_tokens=8, attention_backend=attn_backend
    )

    # Call the method under test
    proposer.load_model(target_model)

    # Verify common interactions
    mock_get_model.assert_called_once()

    # Verify that the lm head is set correctly
    if use_distinct_lm_head:
        assert proposer.model.lm_head is not target_model.lm_head
    else:
        assert proposer.model.lm_head is target_model.lm_head

    # Verify that the embed tokens are set correctly
    # If pp_size is > 1, the embed tokens should be distinct
    if pp_size > 1 or use_distinct_embed_tokens:
        assert proposer.model.model.embed_tokens is not target_model.model.embed_tokens
    else:
        assert proposer.model.model.embed_tokens is target_model.model.embed_tokens