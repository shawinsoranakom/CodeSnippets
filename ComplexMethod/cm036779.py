def test_structured_output_with_reasoning_matrices(
    backend: str,
    tokenizer_mode: str,
    reasoning_parser: str,
    model_name: str,
    speculative_config: dict[str, Any] | None,
    async_scheduling: bool,
):
    if current_platform.is_tpu() and speculative_config:
        pytest.skip("TPU does not support speculative decoding")

    # Use a single LLM instance for several scenarios to
    # speed up the test suite.
    llm = LLM(
        model=model_name,
        # Don't use eager execution on TPUs because we want to test for no
        # recompilation at runtime
        enforce_eager=bool(not current_platform.is_tpu()),
        max_model_len=1024,
        max_num_seqs=16,
        structured_outputs_config=dict(
            backend=backend,
            disable_any_whitespace=backend in {"xgrammar", "guidance"},
            reasoning_parser=reasoning_parser,
        ),
        tokenizer_mode=tokenizer_mode,
        speculative_config=speculative_config,
        async_scheduling=async_scheduling,
    )
    tokenizer = llm.get_tokenizer()
    reasoner = ReasoningParserManager.get_reasoning_parser(reasoning_parser)(
        tokenizer=tokenizer
    )

    reasoning_prompt = "Solve the following math problem step-by-step, then provide the final answer as JSON object with a single key 'result'. Make sure to correct your reasoning if there are any issue should it arise.\nProblem: What is 5 * 8 + 2?"  # noqa: E501
    reasoning_schema = {
        "type": "object",
        "properties": {"result": {"type": "integer"}},
        "required": ["result"],
        "additionalProperties": False,
    }
    if "Qwen3" in model_name:
        reasoning_prompt += "<think>\n"

    sampling_params = SamplingParams(
        temperature=0.1,
        max_tokens=8192,
        structured_outputs=StructuredOutputsParams(json=reasoning_schema),
    )
    outputs = llm.generate(
        [reasoning_prompt],
        sampling_params=sampling_params,
        use_tqdm=True,
    )

    assert outputs is not None
    output = outputs[0]
    assert output is not None and isinstance(output, RequestOutput)
    prompt = output.prompt
    generated_text = output.outputs[0].text
    reasoning, content = run_reasoning_extraction(reasoner, [generated_text])
    print(f"Prompt: {prompt!r}\nReasoning: {reasoning!r}\nContent: {content!r}")

    if "Qwen3" in model_name:
        assert content is not None

    assert reasoning is not None

    if content is not None:
        output_json = json.loads(content)
        jsonschema.validate(instance=output_json, schema=reasoning_schema)