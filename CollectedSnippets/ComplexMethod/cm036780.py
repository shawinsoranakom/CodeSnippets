def test_structured_output_batched_with_non_structured_outputs_requests(
    backend: str,
):
    sample_json_schema = SAMPLE_JSON_SCHEMA
    # Don't use eager execution on TPUs because we want to test for no
    # recompilation at runtime
    enforce_eager = bool(not current_platform.is_tpu())

    llm = LLM(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        enforce_eager=enforce_eager,
        max_model_len=1024,
        structured_outputs_config=StructuredOutputsConfig(
            backend=backend,
            disable_any_whitespace=backend in {"xgrammar", "guidance"},
        ),
    )

    structured_outputs_prompt = (
        "Give an example JSON for an employee profile that fits this "
        "schema. Make the response as short as possible. Schema: "
        f"{sample_json_schema}"
    )

    non_structured_outputs_prompt = "The diameter of the Earth in kilometers is "

    prompts = [structured_outputs_prompt, non_structured_outputs_prompt]
    sampling_params = [
        SamplingParams(
            temperature=1.0,
            max_tokens=400,
            structured_outputs=StructuredOutputsParams(json=sample_json_schema),
        ),
        # No max tokens, temp=0 to assert on contents
        SamplingParams(
            seed=42,
            temperature=0,
            top_p=1.0,
        ),
    ]

    outputs = llm.generate(
        prompts=prompts, sampling_params=sampling_params, use_tqdm=True
    )

    assert outputs is not None

    # Free memory as soon as possible as failed assertions
    # will short circuit and not free up memory
    del llm
    torch.accelerator.empty_cache()
    cleanup_dist_env_and_memory()

    for index, output in enumerate(outputs):
        assert output is not None
        assert isinstance(output, RequestOutput)
        prompt = output.prompt

        generated_text = output.outputs[0].text
        assert generated_text is not None
        print(f"Prompt:\n{prompt!r}\nGenerated text:\n{generated_text!r}")

        if index == 0:
            # First prompt is structured outputs, expect valid JSON
            assert "\n" not in generated_text
            output_json = json.loads(generated_text)
            jsonschema.validate(instance=output_json, schema=sample_json_schema)
        else:
            # Second prompt is not structured outputs, expect valid output
            # Cannot assert on exact output, but we can expect it to be factual
            assert "12,742" in generated_text

            # non-structured outputs requests should not return a valid JSON here
            with pytest.raises(ValueError):
                output_json = json.loads(generated_text)