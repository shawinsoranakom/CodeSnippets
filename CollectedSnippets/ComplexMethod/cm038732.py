async def run_vllm_async(
    requests: list[SampleRequest],
    n: int,
    engine_args: AsyncEngineArgs,
    do_profile: bool,
    disable_detokenize: bool = False,
) -> float:
    from vllm import SamplingParams
    from vllm.entrypoints.openai.api_server import (
        build_async_engine_client_from_engine_args,
    )

    async with build_async_engine_client_from_engine_args(
        engine_args,
    ) as llm:
        model_config = llm.model_config
        assert all(
            model_config.max_model_len
            >= (request.prompt_len + request.expected_output_len)
            for request in requests
        ), (
            "Please ensure that max_model_len is greater than the sum of"
            " prompt_len and expected_output_len for all requests."
        )

        # Add the requests to the engine.
        prompts: list[TextPrompt | TokensPrompt] = []
        sampling_params: list[SamplingParams] = []
        lora_requests: list[LoRARequest | None] = []
        for request in requests:
            prompt = (
                TokensPrompt(prompt_token_ids=request.prompt["prompt_token_ids"])
                if "prompt_token_ids" in request.prompt
                else TextPrompt(prompt=request.prompt)
            )

            if request.multi_modal_data:
                assert isinstance(request.multi_modal_data, dict)
                prompt["multi_modal_data"] = request.multi_modal_data

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
            prompts.append(prompt)
            lora_requests.append(request.lora_request)

        generators = []
        start = time.perf_counter()
        if do_profile:
            await llm.start_profile()
        for i, (prompt, sp, lr) in enumerate(
            zip(prompts, sampling_params, lora_requests)
        ):
            generator = llm.generate(prompt, sp, lora_request=lr, request_id=f"test{i}")
            generators.append(generator)
        all_gens = merge_async_iterators(*generators)
        async for i, res in all_gens:
            pass
        if do_profile:
            await llm.stop_profile()
        end = time.perf_counter()
        return end - start