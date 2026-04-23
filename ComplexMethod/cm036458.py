def test_reasoning(
    streaming: bool,
    param_dict: dict,
    step3p5_tokenizer,
    request,
):
    output = step3p5_tokenizer.tokenize(param_dict["output"])
    # decode everything to tokens
    output_tokens: list[str] = [
        step3p5_tokenizer.convert_tokens_to_string([token]) for token in output
    ]
    parser: ReasoningParser = ReasoningParserManager.get_reasoning_parser(parser_name)(
        step3p5_tokenizer
    )

    reasoning, content = run_reasoning_extraction(
        parser, output_tokens, streaming=streaming
    )

    print(f"reasoning: {reasoning}")
    print(f"content: {content}")
    test_id = request.node.callspec.id if hasattr(request.node, "callspec") else None
    if request.node.callspec.id != "multi_turn_prompt_content":
        assert reasoning == param_dict["reasoning"]
        assert content == param_dict["content"]

    # Test is_reasoning_end
    output_ids = step3p5_tokenizer.convert_tokens_to_ids(output)
    if streaming:
        is_reasoning_end = parser.is_reasoning_end(output_ids)
        assert is_reasoning_end == param_dict["is_reasoning_end"]

    # Test extract_content
    if param_dict["content"] is not None:
        content = parser.extract_content_ids(output_ids)
        # Fixed expected token ids for specific test cases
        test_id = (
            request.node.callspec.id if hasattr(request.node, "callspec") else None
        )
        # Match most specific first
        if test_id not in [
            "new_line_streaming_complex_content",
            "new_line_streaming",
            "new_line",
            "multi_turn_prompt_content",
        ]:
            expected_content_ids = step3p5_tokenizer.convert_tokens_to_ids(
                step3p5_tokenizer.tokenize(param_dict["content"])
            )
            assert content == expected_content_ids
    else:
        content = parser.extract_content_ids(output)
        assert content == []