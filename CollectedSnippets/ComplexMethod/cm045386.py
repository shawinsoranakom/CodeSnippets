async def test_streaming_with_tool_calls_and_reflection(self) -> None:
        """Test streaming with tool calls followed by reflection."""
        model_client = MagicMock()
        model_client.model_info = {"function_calling": True, "vision": False, "family": ModelFamily.GPT_4O}

        call_count = 0

        async def mock_create_stream(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call: tool call
                yield CreateResult(
                    finish_reason="function_calls",
                    content=[FunctionCall(id="1", arguments=json.dumps({"param": "test"}), name="mock_tool_function")],
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                )
            else:
                # Second call: reflection streaming
                yield "Reflection "
                yield "response "
                yield "complete"
                yield CreateResult(
                    finish_reason="stop",
                    content="Reflection response complete",
                    usage=RequestUsage(prompt_tokens=15, completion_tokens=10),
                    cached=False,
                )

        model_client.create_stream = mock_create_stream

        agent = AssistantAgent(
            name="test_agent",
            model_client=model_client,
            tools=[mock_tool_function],
            reflect_on_tool_use=True,
            model_client_stream=True,
        )

        messages: List[Any] = []
        async for message in agent.on_messages_stream(
            [TextMessage(content="Test", source="user")], CancellationToken()
        ):
            messages.append(message)

        # Should have tool call events, execution events, and streaming chunks for reflection
        tool_call_events = [msg for msg in messages if isinstance(msg, ToolCallRequestEvent)]
        tool_exec_events = [msg for msg in messages if isinstance(msg, ToolCallExecutionEvent)]
        chunk_events = [msg for msg in messages if isinstance(msg, ModelClientStreamingChunkEvent)]

        assert len(tool_call_events) == 1
        assert len(tool_exec_events) == 1
        assert len(chunk_events) == 3  # Three reflection chunks
        assert chunk_events[0].content == "Reflection "
        assert chunk_events[1].content == "response "
        assert chunk_events[2].content == "complete"