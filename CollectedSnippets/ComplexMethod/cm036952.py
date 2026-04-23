def test_beam_search_with_concurrency_limit(
    monkeypatch,
    hf_runner,
    vllm_runner,
    example_prompts,
    model: str,
    dtype: str,
    max_tokens: int,
    beam_width: int,
) -> None:
    if current_platform.is_rocm():
        monkeypatch.setenv("VLLM_ROCM_USE_SKINNY_GEMM", "0")

    # example_prompts[1]&[3]&[7] fails due to unknown reason even without
    # concurrency limit. skip them for now.
    example_prompts = example_prompts[:8]
    concurrency_limit = 2
    assert len(example_prompts) > concurrency_limit
    with vllm_runner(model, dtype=dtype, **EXTRA_ENGINE_KWARGS) as vllm_model:
        outputs_with_limit = vllm_model.generate_beam_search(
            example_prompts,
            beam_width,
            max_tokens,
            concurrency_limit=concurrency_limit,
        )
        outputs_without_limit = []

        for i in range(0, len(example_prompts), concurrency_limit):
            outputs_without_limit.extend(
                vllm_model.generate_beam_search(
                    example_prompts[i : i + concurrency_limit],
                    beam_width,
                    max_tokens,
                )
            )

    correct = True
    for i in range(len(example_prompts)):
        output_ids_with_limit, output_texts_with_limit = outputs_with_limit[i]
        output_ids_without_limit, output_texts_without_limit = outputs_without_limit[i]
        for j, (text_with_limit, text_without_limit) in enumerate(
            zip(output_texts_with_limit, output_texts_without_limit)
        ):
            print(f">>>{j}-th with limit output:")
            print(text_with_limit)
            print(f">>>{j}-th without limit output:")
            print(text_without_limit)
        assert len(output_ids_with_limit) == len(output_ids_without_limit)
        for j in range(len(output_ids_with_limit)):
            if output_ids_with_limit[j] != output_ids_without_limit[j]:
                print(
                    f"Test{i} output{j}:\n+limit: {output_ids_with_limit}\n"
                    f"-limit: {output_ids_without_limit}"
                )
                correct = False
    assert correct