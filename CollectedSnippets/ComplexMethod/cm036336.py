def test_stop_string(
    include_stop_str_in_output: bool,
    num_sample_logprobs: int | None,
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
                output_kind=RequestOutputKind.DELTA,
                stop=STOP_STRINGS,
                include_stop_str_in_output=include_stop_str_in_output,
                logprobs=num_sample_logprobs,
                prompt_logprobs=None,
            ),
            pooling_params=None,
        )
        for idx, prompt_tokens in enumerate(dummy_test_vectors.prompt_tokens)
    ]

    engine_core = MockEngineCore(
        tokens_list=dummy_test_vectors.generation_tokens,
        prompts_list=dummy_test_vectors.prompt_tokens,
        generated_logprobs_raw=dummy_test_vectors.generation_logprobs
        if num_sample_logprobs
        else None,
        prompt_logprobs_raw=None,
        request_ids=[req.request_id for req in requests],
    )

    # Add requests to the detokenizer.
    for request, prompt in zip(requests, dummy_test_vectors.prompt_strings):
        output_processor.add_request(request, prompt)

    gen_strings = {}
    gen_tokens = {}
    gen_logprobs = {}
    gen_prompt_logprobs = {}
    gen_cumulative_logprobs = {}
    aborted = []
    while True:
        # Mock output from the EngineCore.
        outputs = engine_core.get_outputs()
        if len(outputs) == 0:
            break

        # Step the Detokenizer.
        processed_outputs = output_processor.process_outputs(outputs)
        request_outputs = processed_outputs.request_outputs
        requests_to_abort = processed_outputs.reqs_to_abort
        for request_output in request_outputs:
            # If aborted, we should not get a request output.
            assert request_output.request_id not in aborted
        aborted.extend(requests_to_abort)

        # Update tracking.
        for request_output in request_outputs:
            if request_output.finished:
                assert request_output.outputs[0].finish_reason == "stop"

            request_id = request_output.request_id
            new_text = request_output.outputs[0].text
            new_tokens = request_output.outputs[0].token_ids
            prompt_logprobs = request_output.prompt_logprobs
            logprobs = request_output.outputs[0].logprobs
            gen_cumulative_logprobs[request_id] = request_output.outputs[
                0
            ].cumulative_logprob
            if request_id not in gen_strings:
                gen_strings[request_id] = new_text
                gen_tokens[request_id] = new_tokens
                gen_logprobs[request_id] = logprobs
                gen_prompt_logprobs[request_id] = prompt_logprobs
            else:
                gen_strings[request_id] += new_text
                gen_tokens[request_id].extend(new_tokens)
                lp = gen_logprobs[request_id]
                plp = gen_prompt_logprobs[request_id]
                if lp:
                    lp.extend(logprobs)
                if plp:
                    plp.extend(prompt_logprobs)

    # Confirmed tracked values matches what we expected.
    for idx, (ref_gen_str, stop_str) in enumerate(
        zip(dummy_test_vectors.generation_strings, STOP_STRINGS)
    ):
        # Request should be aborted (check internal ID in abort list).
        internal_request_id = f"request-{idx}-int"
        assert internal_request_id in aborted

        # Use external ID for collecting outputs
        request_id = f"request-{idx}"

        # Collected values that were generated.
        gen_str = gen_strings[request_id]

        # Construct reference strings.
        stop_str_idx = ref_gen_str.find(stop_str)
        ref_str_exc_stop = ref_gen_str[:stop_str_idx]
        ref_str_inc_stop = ref_gen_str[:stop_str_idx] + stop_str

        if include_stop_str_in_output:
            assert gen_str == ref_str_inc_stop, f"{gen_str=}, {ref_str_inc_stop=}"
        else:
            assert gen_str == ref_str_exc_stop, f"{gen_str=}, {ref_str_exc_stop=}"

    # Confirmed tracked logprobs match what we expect
    _validate_logprobs(
        gen_tokens,
        gen_logprobs,
        gen_prompt_logprobs,
        gen_cumulative_logprobs,
        dummy_test_vectors,
        request_id_list,
        num_sample_logprobs,
        None,
    )

    assert output_processor.get_num_unfinished_requests() == 0
    assert not output_processor.has_unfinished_requests()