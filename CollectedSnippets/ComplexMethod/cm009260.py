def test_extras_with_multiple_fields() -> None:
    """Test that multiple extra fields can be specified together."""

    @tool(
        extras={
            "defer_loading": True,
            "cache_control": {"type": "ephemeral"},
            "input_examples": [{"query": "python files"}],
        }
    )
    def search_code(query: str) -> str:
        """Search code."""
        return f"Code for {query}"

    model = ChatAnthropic(model=MODEL_NAME)  # type: ignore[call-arg]
    model_with_tools = model.bind_tools([search_code])

    payload = model_with_tools._get_request_payload(  # type: ignore[attr-defined]
        "test",
        **model_with_tools.kwargs,  # type: ignore[attr-defined]
    )

    tool_def = None
    for t in payload["tools"]:
        if isinstance(t, dict) and t.get("name") == "search_code":
            tool_def = t
            break

    assert tool_def is not None
    assert tool_def.get("defer_loading") is True
    assert tool_def.get("cache_control") == {"type": "ephemeral"}
    assert "input_examples" in tool_def