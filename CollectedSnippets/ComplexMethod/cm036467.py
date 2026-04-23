def test_reasoning(
    streaming: bool,
    param_dict: dict,
    deepseek_r1_qwen_tokenizer,
):
    output = deepseek_r1_qwen_tokenizer.tokenize(param_dict["output"])
    # decode everything to tokens
    output_tokens: list[str] = [
        deepseek_r1_qwen_tokenizer.convert_tokens_to_string([token]) for token in output
    ]
    parser: ReasoningParser = ReasoningParserManager.get_reasoning_parser(parser_name)(
        deepseek_r1_qwen_tokenizer
    )

    reasoning, content = run_reasoning_extraction(
        parser, output_tokens, streaming=streaming
    )

    assert reasoning == param_dict["reasoning"]
    assert content == param_dict["content"]

    # Test is_reasoning_end
    output_ids = deepseek_r1_qwen_tokenizer.convert_tokens_to_ids(output)
    is_reasoning_end = parser.is_reasoning_end(output_ids)
    assert is_reasoning_end == param_dict["is_reasoning_end"]

    # Test extract_content
    if param_dict["content"] is not None:
        content = parser.extract_content_ids(output_ids)
        assert content == deepseek_r1_qwen_tokenizer.convert_tokens_to_ids(
            deepseek_r1_qwen_tokenizer.tokenize(param_dict["content"])
        )
    else:
        content = parser.extract_content_ids(output)
        assert content == []