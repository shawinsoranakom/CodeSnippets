def test_error_propagation_async_load(fail_scheduler: Scheduler):
    """test invalid_block_ids with fail policy -> FINISHED_ERROR (async load)"""
    num_prompt_blocks = 100
    num_external_computed_blocks = 99
    invalid_block_idx = 50

    num_prompt_tokens = num_prompt_blocks * fail_scheduler.block_size
    num_external_computed_tokens = (
        num_external_computed_blocks * fail_scheduler.block_size
    )

    request = create_request(num_tokens=num_prompt_tokens)
    fail_scheduler.add_request(request=request)

    req_num_new_matched_tokens = {
        request.request_id: num_external_computed_tokens,
    }

    fail_scheduler.connector = Mock()
    fail_scheduler.connector.get_num_new_matched_tokens.side_effect = (
        _make_get_num_new_matched_tokens(req_num_new_matched_tokens, True)
    )
    fail_scheduler.connector.request_finished.return_value = (False, None)
    fail_scheduler.connector.take_events.return_value = ()

    scheduler_output = fail_scheduler.schedule()

    assert len(fail_scheduler.skipped_waiting) == 1
    assert request.status == RequestStatus.WAITING_FOR_REMOTE_KVS
    assert request.num_computed_tokens == num_external_computed_tokens

    (req_block_ids,) = fail_scheduler.kv_cache_manager.get_block_ids(request.request_id)
    invalid_block_ids = {req_block_ids[invalid_block_idx]}
    model_runner_output = create_model_runner_output(
        reqs=[],
        finished_recving=set(),
        invalid_block_ids=invalid_block_ids,
        use_eos=True,
    )

    outputs = fail_scheduler.update_from_output(scheduler_output, model_runner_output)

    assert request.status == RequestStatus.FINISHED_ERROR
    assert request.get_finished_reason() == FinishReason.ERROR

    assert len(outputs) == 1
    engine_outputs = next(iter(outputs.values()))
    assert len(engine_outputs.outputs) == 1
    output = engine_outputs.outputs[0]
    assert output.request_id == request.request_id
    assert output.finish_reason == FinishReason.ERROR

    assert len(fail_scheduler.waiting) == 0
    assert len(fail_scheduler.skipped_waiting) == 0