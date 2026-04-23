def test_dynamic_shapes_compilation(
    monkeypatch,
    model_name,
    shapes_type,
    use_aot_compile,
    use_bytecode_hook,
    evaluate_guards,
):
    """Test that all dynamic shapes types compile successfully"""
    if use_bytecode_hook and shapes_type == DynamicShapesType.UNBACKED:
        pytest.skip("UNBACKED dynamic shapes require VLLM_USE_BYTECODE_HOOK=0")

    if evaluate_guards and shapes_type == DynamicShapesType.UNBACKED:
        pytest.skip("unbacked dynamic shapes do not add guards")

    if evaluate_guards and use_aot_compile:
        pytest.skip("evaluate_guards requires use_aot_compile=0")

    monkeypatch.setenv("VLLM_USE_AOT_COMPILE", use_aot_compile)
    monkeypatch.setenv("VLLM_USE_BYTECODE_HOOK", "1" if use_bytecode_hook else "0")

    prompt = "Hello, my name is"

    print(f"Testing {shapes_type.name} dynamic shapes...")

    # Initialize the model with specific dynamic shapes configuration
    model = LLM(
        model=model_name,
        compilation_config={
            "mode": CompilationMode.VLLM_COMPILE,
            "dynamic_shapes_config": {
                "type": shapes_type.value,
                "evaluate_guards": evaluate_guards,
            },
        },
        max_model_len=1024,
    )

    output = model.generate(prompt)
    result = output[0].outputs[0].text
    # Example of setting the sampling parameters
    tokenizer = get_tokenizer(model_name)
    yes_tokens = tokenizer.encode("yes", add_special_tokens=False)
    no_tokens = tokenizer.encode("no", add_special_tokens=False)
    allowed_ids = list(set(yes_tokens + no_tokens))
    sampling_params = SamplingParams(
        max_tokens=1, temperature=0, allowed_token_ids=allowed_ids
    )

    output = model.generate(
        "answer with yes or no is " + result + " rubbish for prompt " + prompt + "?",
        sampling_params=sampling_params,
    )
    result = output[0].outputs[0].text
    assert result == "yes"

    # Clean up GPU memory
    del model
    gc.collect()
    torch.accelerator.empty_cache()
    torch.accelerator.synchronize()
    print("GPU memory cleared")