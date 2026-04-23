async def test_thought_event_with_handoff(self) -> None:
        """Test that thought events are included in handoff context."""
        model_client = ReplayChatCompletionClient(
            [
                CreateResult(
                    finish_reason="function_calls",
                    content=[
                        FunctionCall(
                            id="1", arguments=json.dumps({"target": "other_agent"}), name="transfer_to_other_agent"
                        )
                    ],
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                    thought="I need to hand this off to another agent",
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
            handoffs=["other_agent"],
            max_tool_iterations=1,
        )

        result = await agent.run(task="Test handoff with thought")

        # Should have ThoughtEvent in inner messages
        thought_events = [msg for msg in result.messages if isinstance(msg, ThoughtEvent)]
        assert len(thought_events) == 1
        assert thought_events[0].content == "I need to hand this off to another agent"

        # Should have handoff message with thought in context
        handoff_message = result.messages[-1]
        assert isinstance(handoff_message, HandoffMessage)
        assert len(handoff_message.context) == 1
        assert isinstance(handoff_message.context[0], AssistantMessage)
        assert handoff_message.context[0].content == "I need to hand this off to another agent"