async def test_anthropic_basic_text_response(self) -> None:
        """Test basic Anthropic integration without tools."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not found in environment variables")

        client = self._get_anthropic_client()

        agent = AssistantAgent(
            name="anthropic_basic_agent",
            model_client=client,
        )

        # Test with a simple task that doesn't require tools
        result = await agent.run(task="What is 2 + 2? Just answer with the number.")

        # Verify that we got a result
        assert result is not None
        assert isinstance(result, TaskResult)
        # Check that we got a text message with content
        assert isinstance(result.messages[-1], TextMessage)
        assert "4" in result.messages[-1].content

        # Check that usage was tracked
        usage = client.total_usage()
        assert usage.prompt_tokens > 0
        assert usage.completion_tokens > 0