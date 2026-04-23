async def test_thought_event_with_reflection(self) -> None:
        """Test that thought events are yielded during reflection."""
        model_client = ReplayChatCompletionClient(
            [
                # Initial tool call with thought
                CreateResult(
                    finish_reason="function_calls",
                    content=[FunctionCall(id="1", arguments=json.dumps({"param": "test"}), name="mock_tool_function")],
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                    thought="Initial thought before tool call",
                ),
                # Reflection with thought
                CreateResult(
                    finish_reason="stop",
                    content="Based on the tool result, here's my response",
                    usage=RequestUsage(prompt_tokens=15, completion_tokens=10),
                    cached=False,
                    thought="Reflection thought after tool execution",
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
            name="test_agent",
            model_client=model_client,
            tools=[mock_tool_function],
            reflect_on_tool_use=True,
            model_client_stream=True,  # Enable streaming
        )

        messages: List[Any] = []
        async for message in agent.on_messages_stream(
            [TextMessage(content="Test", source="user")], CancellationToken()
        ):
            messages.append(message)

        # Should have two ThoughtEvents - one for initial call, one for reflection
        thought_events = [msg for msg in messages if isinstance(msg, ThoughtEvent)]
        assert len(thought_events) == 2

        thought_contents = [event.content for event in thought_events]
        assert "Initial thought before tool call" in thought_contents
        assert "Reflection thought after tool execution" in thought_contents