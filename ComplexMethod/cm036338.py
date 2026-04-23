def test_lora_request_tracking(log_stats: bool, dummy_test_vectors):
    """Test LoRA request lifecycle tracking through waiting -> running -> finished."""
    output_processor = OutputProcessor(
        dummy_test_vectors.tokenizer, log_stats=log_stats
    )
    engine_core_timestamp = time.monotonic()

    # Create LoRA requests
    lora1 = LoRARequest(lora_name="lora-1", lora_int_id=1, lora_path="/path/to/lora1")
    lora2 = LoRARequest(lora_name="lora-2", lora_int_id=2, lora_path="/path/to/lora2")

    # Create requests with different LoRA adapters:
    # - request-0: lora-1
    # - request-1: lora-2
    # - request-2: None (no LoRA)
    lora_assignments = [lora1, lora2, None]
    requests = [
        EngineCoreRequest(
            request_id=f"request-{idx}-int",
            external_req_id=f"request-{idx}",
            prompt_token_ids=prompt_tokens,
            mm_features=None,
            arrival_time=0,
            lora_request=lora_assignments[idx],
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

    # Add all requests to the OutputProcessor
    for request in requests:
        output_processor.add_request(request, None)

    # First iteration: process outputs with QUEUED events
    outputs = EngineCoreOutputs(
        outputs=engine_core.get_outputs(), scheduler_stats=SchedulerStats()
    )
    for output in outputs.outputs:
        output.events = [
            EngineCoreEvent.new_event(EngineCoreEventType.QUEUED, engine_core_timestamp)
        ]

    iteration_stats = IterationStats() if log_stats else None
    output_processor.process_outputs(
        outputs.outputs, engine_core_timestamp, iteration_stats
    )
    output_processor.update_scheduler_stats(outputs.scheduler_stats)

    if log_stats:
        # Verify waiting counts
        assert outputs.scheduler_stats.waiting_lora_adapters.get("lora-1") == 1
        assert outputs.scheduler_stats.waiting_lora_adapters.get("lora-2") == 1
        assert outputs.scheduler_stats.running_lora_adapters.get("lora-1") == 0
        assert outputs.scheduler_stats.running_lora_adapters.get("lora-2") == 0
        # Verify internal state
        assert len(output_processor.lora_states.requests) == 2
        assert "lora-1" in output_processor.lora_states.requests
        assert "lora-2" in output_processor.lora_states.requests
    else:
        # When log_stats=False, no tracking should occur
        assert iteration_stats is None
        assert len(output_processor.lora_states.requests) == 0

    # Second iteration: process outputs with SCHEDULED events
    outputs = EngineCoreOutputs(
        outputs=engine_core.get_outputs(), scheduler_stats=SchedulerStats()
    )
    for output in outputs.outputs:
        output.events = [
            EngineCoreEvent.new_event(
                EngineCoreEventType.SCHEDULED, engine_core_timestamp
            )
        ]

    iteration_stats = IterationStats() if log_stats else None
    output_processor.process_outputs(
        outputs.outputs, engine_core_timestamp, iteration_stats
    )
    output_processor.update_scheduler_stats(outputs.scheduler_stats)

    if log_stats:
        # Verify running counts
        assert outputs.scheduler_stats.waiting_lora_adapters.get("lora-1") == 0
        assert outputs.scheduler_stats.waiting_lora_adapters.get("lora-2") == 0
        assert outputs.scheduler_stats.running_lora_adapters.get("lora-1") == 1
        assert outputs.scheduler_stats.running_lora_adapters.get("lora-2") == 1
    else:
        assert iteration_stats is None
        assert len(output_processor.lora_states.requests) == 0

    # Third iteration: finish request-0 (lora-1)
    outputs = EngineCoreOutputs(
        outputs=engine_core.get_outputs(), scheduler_stats=SchedulerStats()
    )
    # Find and mark request-0-int as finished (it uses lora-1)
    for output in outputs.outputs:
        if output.request_id == "request-0-int":
            output.finish_reason = FinishReason.LENGTH
            break

    iteration_stats = IterationStats() if log_stats else None
    output_processor.process_outputs(
        outputs.outputs, engine_core_timestamp, iteration_stats
    )
    output_processor.update_scheduler_stats(outputs.scheduler_stats)

    if log_stats:
        # lora-1 should be removed since no requests remain
        assert "lora-1" not in output_processor.lora_states.requests
        # lora-2 should still be running
        assert outputs.scheduler_stats.running_lora_adapters.get("lora-2") == 1
        assert len(output_processor.lora_states.requests) == 1
    else:
        assert len(output_processor.lora_states.requests) == 0

    # Fourth iteration: finish request-1 (lora-2)
    outputs = EngineCoreOutputs(
        outputs=engine_core.get_outputs(), scheduler_stats=SchedulerStats()
    )
    # Find and mark request-1-int as finished (it uses lora-2)
    for output in outputs.outputs:
        if output.request_id == "request-1-int":
            output.finish_reason = FinishReason.LENGTH
            break

    iteration_stats = IterationStats() if log_stats else None
    output_processor.process_outputs(
        outputs.outputs, engine_core_timestamp, iteration_stats
    )
    output_processor.update_scheduler_stats(outputs.scheduler_stats)

    if log_stats:
        # lora-2 should be removed since no requests remain
        assert "lora-2" not in output_processor.lora_states.requests
        assert len(outputs.scheduler_stats.running_lora_adapters) == 0
        assert len(output_processor.lora_states.requests) == 0
    else:
        assert len(output_processor.lora_states.requests) == 0

    # Finish the last request (no LoRA)
    outputs = EngineCoreOutputs(
        outputs=engine_core.get_outputs(), scheduler_stats=SchedulerStats()
    )
    # Find and mark request-2-int as finished (it has no LoRA)
    for output in outputs.outputs:
        if output.request_id == "request-2-int":
            output.finish_reason = FinishReason.LENGTH
            break

    iteration_stats = IterationStats() if log_stats else None
    output_processor.process_outputs(
        outputs.outputs, engine_core_timestamp, iteration_stats
    )
    output_processor.update_scheduler_stats(outputs.scheduler_stats)

    # Verify all requests are finished
    assert output_processor.get_num_unfinished_requests() == 0