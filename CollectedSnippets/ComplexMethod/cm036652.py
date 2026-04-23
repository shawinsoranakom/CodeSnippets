def test_models_distributed(
    monkeypatch: pytest.MonkeyPatch,
    hf_runner,
    vllm_runner,
    example_prompts,
    model: str,
    distributed_executor_backend: str,
    attention_backend: str,
    test_suite: str,
    extra_env: dict[str, str],
    enable_prompt_embeds: bool,
) -> None:
    if test_suite != TARGET_TEST_SUITE:
        pytest.skip(f"Skip test for {test_suite}")

    with monkeypatch.context() as monkeypatch_context:
        if (
            model == "meta-llama/Llama-3.2-1B-Instruct"
            and distributed_executor_backend == "ray"
            and attention_backend == ""
            and test_suite == "L4"
            and enable_prompt_embeds
        ):  # noqa
            pytest.skip("enable_prompt_embeds does not work with ray compiled dag.")

        for k, v in extra_env.items():
            monkeypatch_context.setenv(k, v)

        dtype = "half"
        max_tokens = 5

        # NOTE: take care of the order. run vLLM first, and then run HF.
        # vLLM needs a fresh new process without cuda initialization.
        # if we run HF first, the cuda initialization will be done and it
        # will hurt multiprocessing backend with fork method
        # (the default method).
        attention_config = {"backend": attention_backend} if attention_backend else None
        with vllm_runner(
            model,
            dtype=dtype,
            tensor_parallel_size=2,
            distributed_executor_backend=distributed_executor_backend,
            enable_prompt_embeds=enable_prompt_embeds,
            gpu_memory_utilization=0.7,
            attention_config=attention_config,
        ) as vllm_model:
            if enable_prompt_embeds:
                with hf_runner(model, dtype=dtype) as hf_model:
                    with torch.no_grad():
                        prompt_embeds = hf_model.get_prompt_embeddings(example_prompts)
                    vllm_outputs = vllm_model.generate_greedy(prompt_embeds, max_tokens)
                    vllm_outputs = _fix_prompt_embed_outputs(
                        vllm_outputs, hf_model, example_prompts
                    )
                    hf_outputs = hf_model.generate_greedy(example_prompts, max_tokens)
            else:
                vllm_outputs = vllm_model.generate_greedy(example_prompts, max_tokens)
                with hf_runner(model, dtype=dtype) as hf_model:
                    hf_outputs = hf_model.generate_greedy(example_prompts, max_tokens)

    check_outputs_equal(
        outputs_0_lst=hf_outputs,
        outputs_1_lst=vllm_outputs,
        name_0="hf",
        name_1="vllm",
    )