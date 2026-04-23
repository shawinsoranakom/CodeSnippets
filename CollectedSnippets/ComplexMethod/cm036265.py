def test_abort_request_when_structured_output_fsm_cannot_advance():
    scheduler = object.__new__(Scheduler)
    sampling_params = SamplingParams(ignore_eos=True, max_tokens=4)
    sampling_params.update_from_generation_config({}, EOS_TOKEN_ID)

    request = Request(
        request_id="0",
        prompt_token_ids=[0, 1],
        mm_features=None,
        sampling_params=sampling_params,
        pooling_params=None,
    )
    request.structured_output_request = Mock()
    request.structured_output_request.grammar = Mock()
    request.structured_output_request.grammar.accept_tokens.return_value = False
    request.status = RequestStatus.RUNNING
    request.num_computed_tokens = request.num_tokens

    scheduler.perf_metrics = None
    scheduler.connector = None
    scheduler.structured_output_manager = Mock()
    scheduler.structured_output_manager.should_advance.return_value = True
    scheduler.requests = {request.request_id: request}
    scheduler.running = [request]
    scheduler.waiting = Mock()
    scheduler.kv_cache_manager = Mock()
    scheduler.kv_cache_manager.take_events.return_value = None
    scheduler.kv_event_publisher = Mock()
    scheduler.finished_req_ids = set()
    scheduler.finished_req_ids_dict = None
    scheduler.vllm_config = Mock()
    scheduler.vllm_config.model_config.enable_return_routed_experts = False
    scheduler.recompute_kv_load_failures = False
    scheduler.make_stats = Mock(return_value=None)
    scheduler.max_model_len = 128

    def free_request(req: Request, delay_free_blocks: bool = False):
        scheduler.finished_req_ids.add(req.request_id)
        scheduler.requests.pop(req.request_id, None)
        return None

    scheduler._free_request = Mock(side_effect=free_request)

    output = SchedulerOutput(
        scheduled_new_reqs=[],
        scheduled_cached_reqs=CachedRequestData.make_empty(),
        num_scheduled_tokens={request.request_id: 1},
        total_num_scheduled_tokens=1,
        scheduled_encoder_inputs={},
        scheduled_spec_decode_tokens={},
        num_common_prefix_blocks=[],
        finished_req_ids=set(),
        free_encoder_mm_hashes=[],
    )

    model_runner_output = ModelRunnerOutput(
        req_ids=[request.request_id],
        req_id_to_index={request.request_id: 0},
        sampled_token_ids=[[123]],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    engine_core_outputs = scheduler.update_from_output(output, model_runner_output)

    request.structured_output_request.grammar.accept_tokens.assert_called_once_with(
        request.request_id, [123]
    )
    assert request.resumable is False
    assert request.status == RequestStatus.FINISHED_ERROR
    assert request.request_id not in scheduler.requests
    assert not scheduler.running
    scheduler._free_request.assert_called_once_with(request)
    assert len(engine_core_outputs[0].outputs) == 1
    engine_core_output = engine_core_outputs[0].outputs[0]
    assert engine_core_output.request_id == request.request_id
    assert engine_core_output.new_token_ids == [123]
    assert engine_core_output.finish_reason == FinishReason.ERROR