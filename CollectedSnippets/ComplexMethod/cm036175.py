def test_grammar_init_async_and_sync(async_grammar):
    """Test grammar initialization works correctly in both async and sync modes.

    This test validates that the distributed_executor_backend config option
    correctly controls whether grammar compilation happens asynchronously
    (via executor.submit) or synchronously. When set to "external_launcher",
    grammar compilation is synchronous to avoid deadlocks.
    """
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER)
    prompt = tokenizer.encode('{"a": "b"}')

    # Use "external_launcher" for sync mode, None for async mode
    executor_backend = None if async_grammar else "external_launcher"
    vllm_config = VllmConfig(
        model_config=ModelConfig(tokenizer=TOKENIZER),
        structured_outputs_config=StructuredOutputsConfig(backend="guidance"),
        parallel_config=ParallelConfig(distributed_executor_backend=executor_backend),
    )
    structured_output_manager = StructuredOutputManager(vllm_config)

    sampling_params = SamplingParams(
        structured_outputs=StructuredOutputsParams(
            json='{"type": "object"}',
        ),
    )
    sampling_params.structured_outputs._backend = "guidance"
    sampling_params.update_from_generation_config({}, tokenizer.eos_token_id)

    request = Request(
        "test_request",
        prompt_token_ids=prompt,
        sampling_params=sampling_params,
        pooling_params=None,
    )

    structured_output_manager.grammar_init(request)

    # Check the internal _grammar type immediately after init
    # Before _check_grammar_completion is called, async mode should have a Future
    raw_grammar = request.structured_output_request._grammar
    if async_grammar:
        assert isinstance(raw_grammar, Future), (
            "Async mode should store a Future before completion"
        )
    else:
        assert not isinstance(raw_grammar, Future), (
            "Sync mode should store the grammar directly, not a Future"
        )

    # Wait for grammar to be ready (handles both async and sync cases)
    start_time = time.time()
    while not request.structured_output_request._check_grammar_completion():
        if time.time() - start_time > 5:  # 5-second timeout
            pytest.fail("Grammar compilation timed out")
        time.sleep(0.01)

    # After completion, _grammar should no longer be a Future
    assert not isinstance(request.structured_output_request._grammar, Future)

    # Verify grammar is properly initialized and functional
    grammar = request.structured_output_request.grammar
    assert grammar is not None
    assert not grammar.is_terminated()

    # Verify the grammar can accept valid tokens
    assert grammar.accept_tokens(request.request_id, prompt)