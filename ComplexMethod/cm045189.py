async def test_stream_elicitor_basic_functionality() -> None:
    """Test StreamElicitor basic elicit functionality with schema."""
    import io
    from unittest.mock import patch

    read_stream = io.StringIO("accept\n")
    write_stream = io.StringIO()

    elicitor = StreamElicitor(read_stream, write_stream)

    schema = {"type": "object", "properties": {"response": {"type": "string"}}}
    params = mcp_types.ElicitRequestParams(message="Test message", requestedSchema=schema)

    # Mock asyncio.to_thread to return the read value synchronously
    call_responses = ["accept\n", '{"response": "test"}\n']  # action then content for schema
    call_count = {"count": 0}

    def mock_return(*args: Any, **kwargs: Any) -> str:
        result = call_responses[call_count["count"]]
        call_count["count"] += 1
        return result

    with patch("asyncio.to_thread", side_effect=mock_return):
        result = await elicitor.elicit(params)

        assert isinstance(result, mcp_types.ElicitResult)
        assert result.action == "accept"
        assert result.content == {"response": "test"}

        # Check that prompt was written
        written_text = write_stream.getvalue()
        assert "Test message" in written_text
        assert "Choices:" in written_text
        assert "[a]ccept" in written_text
        assert "Input Schema:" in written_text