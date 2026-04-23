def run_embedding_input_test(
    vllm_runner: type[VllmRunner],
    inputs: list[tuple[list[str], PromptImageInput, PromptVideoInput]],
    model: str,
    *,
    dtype: str,
    max_tokens: int,
    num_logprobs: int,
    mm_limit: int,
    tensor_parallel_size: int,
    distributed_executor_backend: str | None = None,
):
    """Inference result should be the same between
    original image/video input and image/video embeddings input.
    """
    from transformers import AutoProcessor

    processor = AutoProcessor.from_pretrained(model)

    # max_model_len should be greater than image_feature_size
    with vllm_runner(
        model,
        runner="generate",
        max_model_len=4000,
        max_num_seqs=3,
        dtype=dtype,
        limit_mm_per_prompt={"image": mm_limit, "video": mm_limit},
        tensor_parallel_size=tensor_parallel_size,
        distributed_executor_backend=distributed_executor_backend,
        default_torch_num_threads=1,
        enable_mm_embeds=True,
    ) as vllm_model:
        outputs_per_case_for_original_input = [
            vllm_model.generate_greedy_logprobs(
                prompts,
                max_tokens,
                num_logprobs=num_logprobs,
                images=images or None,
                videos=videos or None,
            )
            for prompts, images, videos in inputs
        ]

        outputs_per_case_for_embeddings_input = [
            vllm_model.generate_greedy_logprobs(
                prompts,
                max_tokens,
                num_logprobs=num_logprobs,
                images=batch_make_image_embeddings(images, processor, vllm_model)
                if images
                else None,
                videos=batch_make_video_embeddings(videos, processor, vllm_model)
                if videos
                else None,
            )
            for prompts, images, videos in inputs
        ]

    for outputs_for_original_input, outputs_for_embeddings_input in zip(
        outputs_per_case_for_original_input, outputs_per_case_for_embeddings_input
    ):
        check_logprobs_close(
            outputs_0_lst=outputs_for_original_input,
            outputs_1_lst=outputs_for_embeddings_input,
            name_0="original_input",
            name_1="embeddings_input",
        )