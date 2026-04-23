async def test_complete_workflow_with_all_features(self) -> None:
        """Test agent with tools, handoffs, memory, streaming, and reflection."""
        # Setup memory
        memory = MockMemory(["User prefers detailed explanations"])

        # Setup model client with complex workflow
        model_client = ReplayChatCompletionClient(
            [
                # Initial tool call
                CreateResult(
                    finish_reason="function_calls",
                    content=[
                        FunctionCall(id="1", arguments=json.dumps({"param": "analysis"}), name="mock_tool_function")
                    ],
                    usage=RequestUsage(prompt_tokens=20, completion_tokens=10),
                    cached=False,
                    thought="I need to analyze this first",
                ),
                # Reflection result
                CreateResult(
                    finish_reason="stop",
                    content="Based on the analysis, I can provide a detailed response. The user prefers comprehensive explanations.",
                    usage=RequestUsage(prompt_tokens=30, completion_tokens=15),
                    cached=False,
                    thought="I should be thorough based on user preference",
                ),
            ],
            model_info={
                "function_calling": True,
                "vision": False,
                "json_output": False,
                "family": ModelFamily.GPT_4O,
                "structured_output": False,
            },
        )

        agent = AssistantAgent(
            name="comprehensive_agent",
            model_client=model_client,
            tools=[mock_tool_function],
            handoffs=["specialist_agent"],
            memory=[memory],
            reflect_on_tool_use=True,
            model_client_stream=True,
            tool_call_summary_format="Analysis: {result}",
            metadata={"test": "comprehensive"},
        )

        messages: List[Any] = []
        async for message in agent.on_messages_stream(
            [TextMessage(content="Analyze this complex scenario", source="user")], CancellationToken()
        ):
            messages.append(message)

        # Should have all types of events
        memory_events = [msg for msg in messages if isinstance(msg, MemoryQueryEvent)]
        thought_events = [msg for msg in messages if isinstance(msg, ThoughtEvent)]
        tool_events = [msg for msg in messages if isinstance(msg, ToolCallRequestEvent)]
        execution_events = [msg for msg in messages if isinstance(msg, ToolCallExecutionEvent)]
        chunk_events = [msg for msg in messages if isinstance(msg, ModelClientStreamingChunkEvent)]

        assert len(memory_events) > 0
        assert len(thought_events) == 2  # Initial and reflection thoughts
        assert len(tool_events) == 1
        assert len(execution_events) == 1
        assert len(chunk_events) == 0  # No streaming chunks since we removed the string responses

        # Final response should be TextMessage from reflection
        final_response = None
        for msg in reversed(messages):
            if isinstance(msg, Response):
                final_response = msg
                break

        assert final_response is not None
        assert isinstance(final_response.chat_message, TextMessage)
        assert "comprehensive explanations" in final_response.chat_message.content