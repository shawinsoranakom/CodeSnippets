def test_streaming_subcases(param_dict):
    # Get all of the token IDs
    previous_token_ids = (
        tokenizer.encode(param_dict["previous_text"])
        if param_dict["previous_text"] is not None
        else []
    )
    current_token_ids = tokenizer.encode(param_dict["current_text"])
    delta_token_ids = tokenizer.encode(param_dict["delta_text"])

    parser: ReasoningParser = ReasoningParserManager.get_reasoning_parser(parser_name)(
        tokenizer
    )

    response = parser.extract_reasoning_streaming(
        previous_text=param_dict["previous_text"],
        current_text=param_dict["current_text"],
        delta_text=param_dict["delta_text"],
        previous_token_ids=previous_token_ids,
        current_token_ids=current_token_ids,
        delta_token_ids=delta_token_ids,
    )
    # Streaming currently expects at least one of reasoning content / content,
    # so the response should return None in that case.
    if param_dict["reasoning"] is None and param_dict["content"] is None:
        assert response is None
    else:
        assert isinstance(response, DeltaMessage)
        assert param_dict["reasoning"] == response.reasoning
        assert param_dict["content"] == response.content