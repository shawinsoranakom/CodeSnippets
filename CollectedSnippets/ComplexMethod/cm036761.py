def test_stop_reason(vllm_model, example_prompts):
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL)
    stop_token_id = tokenizer.convert_tokens_to_ids(STOP_STR)
    llm = vllm_model.llm

    # test stop token
    outputs = llm.generate(
        example_prompts,
        sampling_params=SamplingParams(
            ignore_eos=True,
            seed=SEED,
            max_tokens=MAX_TOKENS,
            stop_token_ids=[stop_token_id],
        ),
    )
    for output in outputs:
        output = output.outputs[0]
        assert output.finish_reason == "stop"
        assert output.stop_reason == stop_token_id

    # test stop string
    outputs = llm.generate(
        example_prompts,
        sampling_params=SamplingParams(
            ignore_eos=True, seed=SEED, max_tokens=MAX_TOKENS, stop="."
        ),
    )
    for output in outputs:
        output = output.outputs[0]
        assert output.finish_reason == "stop"
        assert output.stop_reason == STOP_STR

    # test EOS token
    outputs = llm.generate(
        example_prompts,
        sampling_params=SamplingParams(seed=SEED, max_tokens=MAX_TOKENS),
    )
    for output in outputs:
        output = output.outputs[0]
        assert output.finish_reason == "length" or (
            output.finish_reason == "stop" and output.stop_reason is None
        )