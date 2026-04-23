def run_awq_test(
    vllm_runner: type[VllmRunner],
    image_assets: ImageTestAssets,
    source_model: str,
    quant_model: str,
    *,
    size_factors: list[float],
    dtype: str,
    max_tokens: int,
    num_logprobs: int,
    tensor_parallel_size: int,
    distributed_executor_backend: str | None = None,
):
    images = [asset.pil_image for asset in image_assets]

    inputs_per_image = [
        (
            [prompt for _ in size_factors],
            [rescale_image_size(image, factor) for factor in size_factors],
        )
        for image, prompt in zip(images, HF_IMAGE_PROMPTS)
    ]

    # NOTE: take care of the order. run vLLM first, and then run HF.
    # vLLM needs a fresh new process without cuda initialization.
    # if we run HF first, the cuda initialization will be done and it
    # will hurt multiprocessing backend with fork method (the default method).

    # max_model_len should be greater than image_feature_size
    with vllm_runner(
        source_model,
        max_model_len=4096,
        dtype=dtype,
        tensor_parallel_size=tensor_parallel_size,
        distributed_executor_backend=distributed_executor_backend,
        enforce_eager=True,
        default_torch_num_threads=1,
    ) as vllm_model:
        source_outputs_per_image = [
            vllm_model.generate_greedy_logprobs(
                prompts, max_tokens, num_logprobs=num_logprobs, images=images
            )
            for prompts, images in inputs_per_image
        ]

    with vllm_runner(
        quant_model,
        quantization="awq",
        max_model_len=4096,
        dtype=dtype,
        tensor_parallel_size=tensor_parallel_size,
        distributed_executor_backend=distributed_executor_backend,
        enforce_eager=True,
        default_torch_num_threads=1,
    ) as vllm_model:
        quant_outputs_per_image = [
            vllm_model.generate_greedy_logprobs(
                prompts, max_tokens, num_logprobs=num_logprobs, images=images
            )
            for prompts, images in inputs_per_image
        ]

    for source_outputs, quant_outputs in zip(
        source_outputs_per_image, quant_outputs_per_image
    ):
        # TODO: Check whether using original CLIPVisionModel can improve
        # consistency against HF
        check_logprobs_close(
            outputs_0_lst=source_outputs,
            outputs_1_lst=quant_outputs,
            name_0="source",
            name_1="awq",
        )