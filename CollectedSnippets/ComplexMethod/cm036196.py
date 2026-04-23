def test_eagle_max_len(
    monkeypatch: pytest.MonkeyPatch, num_speculative_tokens: int, attn_backend: str
):
    if attn_backend == "ROCM_AITER_FA" and current_platform.is_rocm():
        monkeypatch.setenv("VLLM_ROCM_USE_AITER", "1")

    llm = LLM(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        enforce_eager=True,  # For faster initialization.
        speculative_config={
            "method": "eagle",
            "model": "yuhuili/EAGLE-LLaMA3-Instruct-8B",
            "num_speculative_tokens": num_speculative_tokens,
            "max_model_len": 80,
        },
        max_model_len=200,
        attention_config={"backend": attn_backend},
    )
    sampling_params = SamplingParams(max_tokens=200, ignore_eos=True)
    outputs = llm.generate(_PROMPTS, sampling_params)
    for o in outputs:
        assert o.outputs[0].finish_reason == "length", (
            "This test is only meaningful if the output is truncated due to max length"
        )

    sampling_params = SamplingParams(
        max_tokens=200,
        structured_outputs=StructuredOutputsParams(regex="^" + "a b c d e " * 15 + "$"),
    )
    output = llm.generate(_PROMPTS, sampling_params)
    for o in output:
        assert o.prompt_token_ids is not None
        assert (
            len(o.prompt_token_ids)
            < 80
            < len(o.prompt_token_ids) + len(o.outputs[0].token_ids)
            <= 200
        ), (
            "This test is only meaningful if the output "
            "is longer than the eagle max length"
        )
        assert o.outputs[0].text == "a b c d e " * 15