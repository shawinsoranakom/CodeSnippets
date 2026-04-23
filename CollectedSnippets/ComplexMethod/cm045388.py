async def test_state_persistence_across_interactions(self) -> None:
        """Test that agent state persists correctly across multiple interactions."""
        model_client = ReplayChatCompletionClient(
            [
                # First interaction
                CreateResult(
                    finish_reason="stop",
                    content="First response",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                ),
                # Second interaction
                CreateResult(
                    finish_reason="stop",
                    content="Second response, remembering context",
                    usage=RequestUsage(prompt_tokens=15, completion_tokens=8),
                    cached=False,
                ),
            ],
            model_info={
                "function_calling": False,
                "vision": False,
                "json_output": False,
                "family": ModelFamily.GPT_4O,
                "structured_output": False,
            },
        )

        agent = AssistantAgent(
            name="stateful_agent",
            model_client=model_client,
            system_message="Remember previous conversations",
        )

        # First interaction
        result1 = await agent.run(task="First task")
        final_message_1 = result1.messages[-1]
        assert isinstance(final_message_1, TextMessage)
        assert final_message_1.content == "First response"

        # Save state
        state = await agent.save_state()
        assert "llm_context" in state

        # Second interaction
        result2 = await agent.run(task="Second task, referring to first")
        # Fix line 2730 - properly access content on TextMessage
        final_message_2 = result2.messages[-1]
        assert isinstance(final_message_2, TextMessage)
        assert final_message_2.content == "Second response, remembering context"

        # Verify context contains both interactions
        context_messages = await agent.model_context.get_messages()
        user_messages = [
            msg for msg in context_messages if hasattr(msg, "source") and getattr(msg, "source", None) == "user"
        ]
        assert len(user_messages) == 2