def run_vllm(
    requests: list[SampleRequest],
    n: int,
    engine_args: EngineArgs,
    do_profile: bool,
    disable_detokenize: bool = False,
) -> tuple[float, list[RequestOutput] | None]:
    from vllm import LLM, SamplingParams

    llm = LLM.from_engine_args(engine_args)
    assert all(
        llm.llm_engine.model_config.max_model_len
        >= (request.prompt_len + request.expected_output_len)
        for request in requests
    ), (
        "Please ensure that max_model_len is greater than the sum of"
        " prompt_len and expected_output_len for all requests."
    )
    # Add the requests to the engine.
    prompts: list[TextPrompt | TokensPrompt] = []
    sampling_params: list[SamplingParams] = []
    for request in requests:
        prompt = (
            TokensPrompt(prompt_token_ids=request.prompt["prompt_token_ids"])
            if "prompt_token_ids" in request.prompt
            else TextPrompt(prompt=request.prompt)
        )
        if request.multi_modal_data:
            assert isinstance(request.multi_modal_data, dict)
            prompt["multi_modal_data"] = request.multi_modal_data
        prompts.append(prompt)

        sampling_params.append(
            SamplingParams(
                n=n,
                temperature=1.0,
                top_p=1.0,
                ignore_eos=True,
                max_tokens=request.expected_output_len,
                detokenize=not disable_detokenize,
            )
        )
    lora_requests: list[LoRARequest] | None = None
    if engine_args.enable_lora:
        lora_requests = [request.lora_request for request in requests]

    use_beam_search = False

    outputs = None
    if not use_beam_search:
        start = time.perf_counter()
        if do_profile:
            llm.start_profile()
        outputs = llm.generate(
            prompts, sampling_params, lora_request=lora_requests, use_tqdm=True
        )
        if do_profile:
            llm.stop_profile()
        end = time.perf_counter()
    else:
        assert lora_requests is None, "BeamSearch API does not support LoRA"
        prompts = [request.prompt for request in requests]
        # output_len should be the same for all requests.
        output_len = requests[0].expected_output_len
        for request in requests:
            assert request.expected_output_len == output_len
        start = time.perf_counter()
        if do_profile:
            llm.start_profile()
        llm.beam_search(
            prompts,
            BeamSearchParams(
                beam_width=n,
                max_tokens=output_len,
                ignore_eos=True,
            ),
        )
        if do_profile:
            llm.stop_profile()
        end = time.perf_counter()
    return end - start, outputs