def test_tool_parser_adjust_request_builds_valid_response_text_config() -> None:
    """``ToolParser.adjust_request`` must produce a ``ResponseTextConfig``
    whose dumped form contains the JSON schema under the ``schema`` alias
    and does not leak the unrelated ``"Response format for tool calling"``
    description string that the previous two-step construction injected.
    """
    parser = ToolParser.__new__(ToolParser)
    parser.model_tokenizer = None

    request = _build_responses_request(tool_choice="required")
    ToolParser.adjust_request(parser, request)

    assert request.text is not None
    assert request.text.format is not None
    assert request.text.format.type == "json_schema"

    dump: dict[str, Any] = request.text.model_dump(mode="json", by_alias=True)
    fmt = dump.get("format") or {}
    assert fmt.get("type") == "json_schema"
    assert fmt.get("name") == "tool_calling_response"
    assert fmt.get("strict") is True
    # Nested config must be present under the alias. Two-step Pydantic v2
    # construction could drop it from __fields_set__.
    assert "schema" in fmt and isinstance(fmt["schema"], dict)
    # The old code passed a wrong-purpose string; valid field should now
    # either be absent or None (the openai-python default).
    assert fmt.get("description") in (None, "")