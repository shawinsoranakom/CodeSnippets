def test_incremental_detokenization(
    request_output_kind: RequestOutputKind,
    stream_interval: int,
    dummy_test_vectors,
):
    output_processor = OutputProcessor(
        dummy_test_vectors.tokenizer, log_stats=False, stream_interval=stream_interval
    )

    # Make N requests.
    requests = [
        EngineCoreRequest(
            request_id=f"request-{idx}-int",
            external_req_id=f"request-{idx}",
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
            ),
            pooling_params=None,
        )
        for idx, prompt_tokens in enumerate(dummy_test_vectors.prompt_tokens)
    ]

    engine_core = MockEngineCore(
        tokens_list=dummy_test_vectors.generation_tokens,
        prompts_list=dummy_test_vectors.prompt_tokens,
        request_ids=[req.request_id for req in requests],
    )

    # Add requests to the detokenizer.
    for request, prompt in zip(requests, dummy_test_vectors.prompt_strings):
        output_processor.add_request(request, prompt)

    gen_strings = {}
    gen_tokens = {}
    while True:
        # Mock output from the EngineCore.
        outputs = engine_core.get_outputs()
        if len(outputs) == 0:
            break

        # Step the Detokenizer.
        processed_outputs = output_processor.process_outputs(outputs)
        request_outputs = processed_outputs.request_outputs
        requests_to_abort = processed_outputs.reqs_to_abort
        assert len(requests_to_abort) == 0

        # Update tracking.
        for request_output in request_outputs:
            request_id = request_output.request_id
            new_text = request_output.outputs[0].text
            new_tokens = request_output.outputs[0].token_ids
            if request_id not in gen_strings:
                gen_strings[request_id] = new_text
                gen_tokens[request_id] = new_tokens
                if request_output_kind == RequestOutputKind.DELTA:
                    assert len(new_tokens) == 1, f"{len(new_tokens)=}"
            else:
                gen_strings[request_id] += new_text
                gen_tokens[request_id].extend(new_tokens)
                if (
                    request_output_kind == RequestOutputKind.DELTA
                    and not request_output.finished
                ):
                    assert len(new_tokens) >= stream_interval, (
                        f"{len(new_tokens)=}, {stream_interval=}"
                    )

    # Confirmed tracked values matches what we expected.
    for idx, (ref_gen_str, ref_gen_toks) in enumerate(
        zip(dummy_test_vectors.generation_strings, dummy_test_vectors.generation_tokens)
    ):
        gen_str = gen_strings[f"request-{idx}"]
        gen_toks = gen_tokens[f"request-{idx}"]

        assert gen_str == ref_gen_str, f"{gen_str=}, {ref_gen_str=}"
        assert gen_toks == ref_gen_toks, f"{gen_toks=}, {ref_gen_toks=}"

    assert output_processor.get_num_unfinished_requests() == 0
    assert not output_processor.has_unfinished_requests()