async def test_streaming_with_empty_chunks(self) -> None:
        """Test streaming with empty chunks."""
        model_client = MagicMock()
        model_client.model_info = {"function_calling": False, "vision": False, "family": ModelFamily.GPT_4O}

        async def mock_create_stream(*args: Any, **kwargs: Any) -> Any:
            yield ""  # Empty chunk
            yield "content"
            yield ""  # Another empty chunk
            yield CreateResult(
                finish_reason="stop",
                content="content",
                usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                cached=False,
            )

        model_client.create_stream = mock_create_stream

        agent = AssistantAgent(
            name="test_agent",
            model_client=model_client,
            model_client_stream=True,
        )

        messages: List[Any] = []
        async for message in agent.on_messages_stream(
            [TextMessage(content="Test", source="user")], CancellationToken()
        ):
            messages.append(message)

        # Should handle empty chunks gracefully
        chunk_events = [msg for msg in messages if isinstance(msg, ModelClientStreamingChunkEvent)]
        assert len(chunk_events) == 3  # Including empty chunks
        assert chunk_events[0].content == ""
        assert chunk_events[1].content == "content"
        assert chunk_events[2].content == ""