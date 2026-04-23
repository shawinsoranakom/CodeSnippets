def run_multimodal_gguf_test(
    hf_runner: type[HfRunner],
    vllm_runner: type[VllmRunner],
    model: GGUFMMTestConfig,
    dtype: str,
    max_tokens: int,
    num_logprobs: int,
):
    # Load images at runtime (inside subprocess) to avoid pickle issues
    images = [ImageAsset(name).pil_image for name in model.image_names]
    size_factors = [0.25, 0.5, 1.0]
    inputs_per_image = [
        (
            [prompt for _ in size_factors],
            [rescale_image_size(image, factor) for factor in size_factors],
        )
        for image, prompt in zip(images, model.prompt)
    ]

    # NOTE: Run vLLM first to avoid CUDA init issues with multiprocessing fork.
    # Run GGUF model via vLLM.
    with (
        set_default_torch_num_threads(1),
        vllm_runner(
            model_name=model.gguf_model,
            enforce_eager=True,
            tokenizer_name=model.original_model,
            dtype=dtype,
            max_model_len=model.max_model_len,
            mm_processor_kwargs=model.mm_processor_kwargs,
        ) as gguf_model,
    ):
        gguf_outputs_per_case = [
            gguf_model.generate_greedy_logprobs(
                prompts,
                max_tokens,
                num_logprobs=num_logprobs,
                images=images,
            )
            for prompts, images in inputs_per_image
        ]

    # Then run HfRunner for HuggingFace baseline comparison.
    with hf_runner(
        model.original_model,
        dtype=dtype,
        auto_cls=AutoModelForImageTextToText,
    ) as hf_model:
        hf_outputs_per_case = [
            hf_model.generate_greedy_logprobs_limit(
                prompts,
                max_tokens,
                num_logprobs=num_logprobs,
                images=images,
            )
            for prompts, images in inputs_per_image
        ]

    for hf_outputs, gguf_outputs in zip(hf_outputs_per_case, gguf_outputs_per_case):
        check_logprobs_close(
            outputs_0_lst=hf_outputs,
            outputs_1_lst=gguf_outputs,
            name_0="hf",
            name_1="gguf",
        )