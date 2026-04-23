async def test_anthropic_tool_call_loop_max_iterations_10(self) -> None:
        """Test Anthropic integration with tool call loop and max_tool_iterations=10."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not found in environment variables")

        client = self._get_anthropic_client()

        agent = AssistantAgent(
            name="anthropic_test_agent",
            model_client=client,
            tools=[mock_tool_function],
            max_tool_iterations=10,
        )

        # Test with a task that might require tool calls
        result = await agent.run(
            task="Use the mock_tool_function to process the text 'hello world'. Then provide a summary."
        )

        # Verify that we got a result
        assert result is not None
        assert isinstance(result, TaskResult)
        assert len(result.messages) > 0
        # Check that the last message is a non-tool call.
        assert isinstance(result.messages[-1], TextMessage)
        # Check that a tool call was made
        tool_calls = [msg for msg in result.messages if isinstance(msg, ToolCallRequestEvent)]
        assert len(tool_calls) > 0

        # Check that usage was tracked
        usage = client.total_usage()
        assert usage.prompt_tokens > 0
        assert usage.completion_tokens > 0