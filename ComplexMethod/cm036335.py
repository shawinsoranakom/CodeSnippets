def test_stop_token(
    include_stop_str_in_output: bool,
    num_sample_logprobs: int | None,
    stop_token_type: str,
    ignore_eos: bool,
    dummy_test_vectors,
):
    """Test output processor EOS/stop token handling.

    Send mock engine core request to mock engine core and pass core outputs
    to output processor. Validate output processor tokens, text and
    (if enabled) sample logprobs. Batch-size one.

    The test emulates a scenario where a model outputs text tokens followed
    by two identical control tokens:
    <token><token>...<token><control><control>

    If EOS is under test, the control tokens are EOS; otherwise, they are
    some other token id.

    Test behavior:

    * If EOS is under test and `ignore_eos=True`, the detokenized string
      should be <token><token>...<token><control><control> and the finish
      reason should be "length" (i.e. no stop occurs)

    * else, if `include_stop_str_in_output==True`, the detokenized
      string should be <token><token>...<token><control> and the finish
      reason should be "stop" (i.e. first control token causes stop
      and is represented in output text)

    * else, the detokenized string should be
      <token><token>...<token> and the finish reason should be "stop"
      (i.e. first control token causes stop but is not represented
      in output text.)

    Note: some test details are tuned for meta-llama/Llama-3.2-1B,
    another model should work only if the test is modified.

    Args:
        include_stop_str_in_output: stop token str appears in output text
        num_sample_logprobs: number of sample logprobs (`None` for no logprobs)
        stop_token_type: "eos_token_id" for EOS, "stop_token_ids" for stop token
        ignore_eos: if True, EOS stops are disabled
        dummy_test_vectors: dummy engine core outputs and other data structures
    """
    model_id = dummy_test_vectors.tokenizer.name_or_path
    if model_id != "meta-llama/Llama-3.2-1B":
        raise AssertionError(
            f"Test requires meta-llama/Llama-3.2-1B but {model_id} is in use."
        )
    do_logprobs = num_sample_logprobs is not None
    # EOS under test; if False, stop_token_ids under test
    is_eos_test = stop_token_type == "eos_token_id"
    # EOS under test but ignore_eos enabled
    is_eos_ignore_test = is_eos_test and ignore_eos
    eos_token_id = (
        dummy_test_vectors.tokenizer.eos_token_id if is_eos_test else None
    )  # '<|end_of_text|>'
    stop_token_ids = [128009] if not is_eos_test else None  # '<|eot_id|>'

    output_processor = OutputProcessor(dummy_test_vectors.tokenizer, log_stats=False)
    # Dummy engine core outputs, with control tokens suffixed to test stops
    suffix_token = [eos_token_id] if is_eos_test else stop_token_ids
    assert suffix_token is not None and isinstance(suffix_token[0], int)
    generation_string = dummy_test_vectors.generation_strings[0]
    generation_tokens = dummy_test_vectors.generation_tokens[0] + 2 * suffix_token
    if do_logprobs:
        generation_logprobs = dummy_test_vectors.generation_logprobs[0] + 2 * [
            dummy_test_vectors.generation_logprobs[0][-1]
        ]
    prompt_string = dummy_test_vectors.prompt_strings[0]
    prompt_tokens = dummy_test_vectors.prompt_tokens[0]

    sampling_params = SamplingParams(
        skip_special_tokens=False,
        spaces_between_special_tokens=False,
        output_kind=RequestOutputKind.DELTA,
        stop=[],
        stop_token_ids=stop_token_ids,
        include_stop_str_in_output=include_stop_str_in_output,
        logprobs=num_sample_logprobs,
        prompt_logprobs=None,
        ignore_eos=ignore_eos,
    )
    sampling_params.update_from_generation_config({}, eos_token_id)

    # Make request.
    request_id = "request-0"
    request = EngineCoreRequest(
        request_id=request_id,
        external_req_id=request_id + "-ext",
        prompt_token_ids=prompt_tokens,
        mm_features=None,
        arrival_time=0,
        lora_request=None,
        cache_salt=None,
        data_parallel_rank=None,
        sampling_params=sampling_params,
        pooling_params=None,
    )

    engine_core = MockEngineCore(
        tokens_list=[generation_tokens],
        prompts_list=dummy_test_vectors.prompt_tokens,
        generated_logprobs_raw=[generation_logprobs] if do_logprobs else None,
        prompt_logprobs_raw=None,
        eos_token_id=sampling_params.eos_token_id,
        stop_token_ids=sampling_params.stop_token_ids,
        request_ids=[request.request_id],
    )

    # Add request to the detokenizer.
    output_processor.add_request(request, prompt_string)

    # Loop over engine core steps; run output processor
    gen_string = ""
    gen_tokens = []
    gen_logprobs = []
    while True:
        # Mock output from the EngineCore.
        outputs = engine_core.get_outputs()
        if len(outputs) == 0:
            break

        # Step the Detokenizer.
        processed_outputs = output_processor.process_outputs(outputs)
        request_outputs = processed_outputs.request_outputs
        assert len(request_outputs) == 1
        # Stop token does not rely on abort
        assert not processed_outputs.reqs_to_abort

        # Update tracking.
        request_output = request_outputs[0]
        if request_output.finished:
            finish_reason = "length" if is_eos_ignore_test else "stop"
            assert request_output.outputs[0].finish_reason == finish_reason

        gen_string += request_output.outputs[0].text
        gen_tokens.extend(request_output.outputs[0].token_ids)
        if do_logprobs:
            gen_logprobs.extend(request_output.outputs[0].logprobs)

    # Validate generated text
    control_token = "<|end_of_text|>" if is_eos_test else "<|eot_id|>"
    if is_eos_ignore_test:
        # Length-based stop; expect full string
        ref_str = generation_string + 2 * control_token
    elif include_stop_str_in_output:
        # Stop token triggered; include in output
        ref_str = generation_string + control_token
    else:
        # Stop token triggered but not in output
        ref_str = generation_string
    assert gen_string == ref_str, f"{gen_string=}, {ref_str=}"

    if do_logprobs:
        # Validate number of sample logprobs
        num_tokens = len(gen_tokens)
        num_logprobs = len(gen_logprobs)
        assert num_tokens == num_logprobs, (
            f"Token count ({num_tokens}) != logprobs count ({num_logprobs})"
        )

    # Check requests are finished
    assert output_processor.get_num_unfinished_requests() == 0
    assert not output_processor.has_unfinished_requests()