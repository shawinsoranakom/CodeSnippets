def test_adjust_request_tool_choice_with_json_schema_factory_routing(
    mistral_tool_parser: MistralToolParser,
    tool_choice: str,
    expected_method: str,
    not_called_method: str | None,
) -> None:
    request = _make_request(
        tool_choice=tool_choice,
        structured_outputs=StructuredOutputsParams(json='{"type": "object"}'),
    )
    factory = mistral_tool_parser.model_tokenizer.grammar_factory

    patches = {
        expected_method: patch.object(
            factory,
            expected_method,
            wraps=getattr(factory, expected_method),
        ),
    }
    if not_called_method:
        patches[not_called_method] = patch.object(
            factory,
            not_called_method,
            wraps=getattr(factory, not_called_method),
        )

    with patches[expected_method] as mock_expected:
        ctx = patches[not_called_method] if not_called_method else None
        if ctx:
            with ctx as mock_not_called:
                result = mistral_tool_parser.adjust_request(request)
                mock_not_called.assert_not_called()
        else:
            result = mistral_tool_parser.adjust_request(request)

        mock_expected.assert_called_once()
        assert mock_expected.call_args.kwargs["json_schema"] == {"type": "object"}

    assert result.structured_outputs is not None
    assert isinstance(result.structured_outputs.grammar, str)
    assert len(result.structured_outputs.grammar) > 0