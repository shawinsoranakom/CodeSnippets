def test_classify_models(
    hf_runner,
    vllm_runner,
    example_prompts,
    model: str,
    dtype: str,
) -> None:
    # example_prompts is too short for testing prefix_caching
    example_prompts = [s * 10 for s in example_prompts]

    with vllm_runner(
        model, max_model_len=512, dtype=dtype, enable_prefix_caching=True
    ) as vllm_model:
        vllm_config = vllm_model.llm.llm_engine.vllm_config
        cache_config = vllm_config.cache_config
        assert cache_config.enable_prefix_caching

        # First Run
        vllm_model.classify(example_prompts)

        # assert prefix_caching works
        pooling_outputs = vllm_model.llm.encode(
            example_prompts, pooling_task="classify"
        )
        for output in pooling_outputs:
            assert output.num_cached_tokens > 0
        vllm_outputs = [req_output.outputs.data for req_output in pooling_outputs]

    with hf_runner(
        model, dtype=dtype, auto_cls=AutoModelForSequenceClassification
    ) as hf_model:
        hf_outputs = hf_model.classify(example_prompts)

    for hf_output, vllm_output in zip(hf_outputs, vllm_outputs):
        hf_output = torch.tensor(hf_output)
        vllm_output = torch.tensor(vllm_output)

        assert torch.allclose(
            hf_output, vllm_output, 1e-3 if dtype == "float" else 1e-2
        )