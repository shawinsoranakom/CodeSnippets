async def test_thought_event_with_tool_call_loop(self) -> None:
        """Test that thought events are yielded in tool call loops."""
        model_client = ReplayChatCompletionClient(
            [
                # First tool call with thought
                CreateResult(
                    finish_reason="function_calls",
                    content=[FunctionCall(id="1", arguments=json.dumps({"param": "first"}), name="mock_tool_function")],
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                    thought="First iteration thought",
                ),
                # Second tool call with thought
                CreateResult(
                    finish_reason="function_calls",
                    content=[
                        FunctionCall(id="2", arguments=json.dumps({"param": "second"}), name="mock_tool_function")
                    ],
                    usage=RequestUsage(prompt_tokens=12, completion_tokens=5),
                    cached=False,
                    thought="Second iteration thought",
                ),
                # Final response with thought
                CreateResult(
                    finish_reason="stop",
                    content="Loop completed",
                    usage=RequestUsage(prompt_tokens=15, completion_tokens=10),
                    cached=False,
                    thought="Final completion thought",
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
            max_tool_iterations=3,
        )

        messages: List[Any] = []
        async for message in agent.on_messages_stream(
            [TextMessage(content="Test", source="user")], CancellationToken()
        ):
            messages.append(message)

        # Should have three ThoughtEvents - one for each iteration
        thought_events = [msg for msg in messages if isinstance(msg, ThoughtEvent)]
        assert len(thought_events) == 3

        thought_contents = [event.content for event in thought_events]
        assert "First iteration thought" in thought_contents
        assert "Second iteration thought" in thought_contents
        assert "Final completion thought" in thought_contents