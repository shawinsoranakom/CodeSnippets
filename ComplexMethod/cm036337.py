def test_iteration_stats(dummy_test_vectors):
    output_processor = OutputProcessor(dummy_test_vectors.tokenizer, log_stats=True)
    engine_core_timestamp = time.monotonic()

    # Make N requests.
    requests = [
        EngineCoreRequest(
            request_id=f"request-{idx}",
            external_req_id=f"request-{idx}-ext",
            prompt_token_ids=prompt_tokens,
            mm_features=None,
            arrival_time=0,
            lora_request=None,
            cache_salt=None,
            data_parallel_rank=None,
            sampling_params=SamplingParams(),
            pooling_params=None,
        )
        for idx, prompt_tokens in enumerate(dummy_test_vectors.prompt_tokens)
    ]

    engine_core = MockEngineCore(
        dummy_test_vectors.generation_tokens,
        dummy_test_vectors.prompt_tokens,
        request_ids=[req.request_id for req in requests],
    )

    # Add all requests except one to the OutputProcessor.
    num_active = len(dummy_test_vectors.generation_tokens) - 1
    for request in requests[:num_active]:
        output_processor.add_request(request, None)
    inactive_request = requests[num_active]

    # First iteration has 2 prefills.
    outputs = engine_core.get_outputs(num_active)
    iteration_stats = IterationStats()
    output_processor.process_outputs(outputs, engine_core_timestamp, iteration_stats)
    total_prompt_tokens = sum(
        [
            len(prompt_tokens)
            for prompt_tokens in dummy_test_vectors.prompt_tokens[:num_active]
        ]
    )

    assert iteration_stats.num_prompt_tokens == total_prompt_tokens
    assert iteration_stats.num_generation_tokens == num_active

    # Just decodes in this step.
    outputs = engine_core.get_outputs(num_active)
    iteration_stats = IterationStats()
    output_processor.process_outputs(outputs, engine_core_timestamp, iteration_stats)

    assert iteration_stats.num_prompt_tokens == 0
    assert iteration_stats.num_generation_tokens == num_active

    # Add a new request - prefill and 2 decodes in this step.
    output_processor.add_request(inactive_request, None)
    num_active += 1
    outputs = engine_core.get_outputs(num_active)
    iteration_stats = IterationStats()
    output_processor.process_outputs(outputs, engine_core_timestamp, iteration_stats)
    total_prompt_tokens = len(dummy_test_vectors.prompt_tokens[num_active - 1])

    assert iteration_stats.num_prompt_tokens == total_prompt_tokens
    assert iteration_stats.num_generation_tokens == num_active

    # Just decodes in this step.
    outputs = engine_core.get_outputs(num_active)
    iteration_stats = IterationStats()
    output_processor.process_outputs(outputs, engine_core_timestamp, iteration_stats)

    assert iteration_stats.num_prompt_tokens == 0
    assert iteration_stats.num_generation_tokens == num_active