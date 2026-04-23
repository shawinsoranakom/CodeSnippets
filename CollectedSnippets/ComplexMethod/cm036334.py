def test_logprobs_processor(
    request_output_kind: RequestOutputKind,
    num_sample_logprobs: int | None,
    num_prompt_logprobs: int | None,
    dummy_test_vectors,
):
    output_processor = OutputProcessor(dummy_test_vectors.tokenizer, log_stats=False)

    # Make N requests.
    request_id_list = [
        f"request-{idx}" for idx in range(len(dummy_test_vectors.prompt_strings))
    ]
    requests = [
        EngineCoreRequest(
            request_id=request_id_list[idx] + "-int",
            external_req_id=request_id_list[idx],
            prompt_token_ids=prompt_tokens,
            mm_features=None,
            arrival_time=0,
            lora_request=None,
            cache_salt=None,
            data_parallel_rank=None,
            sampling_params=SamplingParams(
                skip_special_tokens=False,
                spaces_between_special_tokens=False,
                output_kind=request_output_kind,
                stop=[],
                include_stop_str_in_output=False,
                logprobs=num_sample_logprobs,
                prompt_logprobs=num_prompt_logprobs,
            ),
            pooling_params=None,
        )
        for idx, prompt_tokens in enumerate(dummy_test_vectors.prompt_tokens)
    ]

    engine_core = MockEngineCore(
        tokens_list=dummy_test_vectors.generation_tokens,
        prompts_list=dummy_test_vectors.prompt_tokens,
        generated_logprobs_raw=None
        if num_sample_logprobs is None
        else dummy_test_vectors.generation_logprobs,
        prompt_logprobs_raw=None
        if num_prompt_logprobs is None
        else dummy_test_vectors.prompt_logprobs,
        request_ids=[req.request_id for req in requests],
    )

    # Add requests to the detokenizer.
    for request, prompt in zip(requests, dummy_test_vectors.prompt_strings):
        output_processor.add_request(request, prompt)

    gen_tokens = {}
    gen_logprobs = {}
    gen_prompt_logprobs = {}
    gen_cumulative_logprobs = {}
    while True:
        # Mock output from the EngineCore.
        outputs = engine_core.get_outputs()
        if len(outputs) == 0:
            break

        # Step the logprobs processor.
        processed_outputs = output_processor.process_outputs(outputs)
        request_outputs = processed_outputs.request_outputs
        requests_to_abort = processed_outputs.reqs_to_abort
        assert len(requests_to_abort) == 0

        # Update tracking.
        for request_output in request_outputs:
            request_id = request_output.request_id
            new_tokens = request_output.outputs[0].token_ids
            prompt_logprobs = request_output.prompt_logprobs
            logprobs = request_output.outputs[0].logprobs
            gen_cumulative_logprobs[request_id] = request_output.outputs[
                0
            ].cumulative_logprob
            if request_id not in gen_logprobs:
                # Start tracking sample and prompt logprobs for this request
                gen_tokens[request_id] = new_tokens
                gen_logprobs[request_id] = logprobs
                gen_prompt_logprobs[request_id] = prompt_logprobs
            else:
                # Extend logprobs tracker
                gen_tokens[request_id].extend(new_tokens)
                lp = gen_logprobs[request_id]
                plp = gen_prompt_logprobs[request_id]
                if lp:
                    lp.extend(logprobs)
                if plp:
                    plp.extend(prompt_logprobs)

    # Confirmed tracked logprobs match what we expect
    _validate_logprobs(
        gen_tokens,
        gen_logprobs,
        gen_prompt_logprobs,
        gen_cumulative_logprobs,
        dummy_test_vectors,
        request_id_list,
        num_sample_logprobs,
        num_prompt_logprobs,
    )

    assert output_processor.get_num_unfinished_requests() == 0
    assert not output_processor.has_unfinished_requests()