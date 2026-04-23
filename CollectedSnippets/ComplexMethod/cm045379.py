async def test_memory_persistence(self) -> None:
        """Test memory persistence across multiple sessions.

        Verifies:
        1. Memory content persists between sessions
        2. Memory updates are preserved
        3. Context is properly restored
        4. Memory query events are generated correctly
        """
        # Create memory with initial content
        memory = MockMemory(contents=["Initial memory"])

        # Create model client
        model_client = ReplayChatCompletionClient(
            [
                CreateResult(
                    finish_reason="stop",
                    content="Response using memory",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                ),
                CreateResult(
                    finish_reason="stop",
                    content="Response with updated memory",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
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

        # Create agent with memory
        agent = AssistantAgent(name="memory_test_agent", model_client=model_client, memory=[memory])

        # First session
        result1 = await agent.run(task="First task")
        state = await agent.save_state()

        # Add new memory content
        await memory.add(MemoryContent(content="New memory", mime_type="text/plain"))

        # Create new agent and restore state
        new_agent = AssistantAgent(name="memory_test_agent", model_client=model_client, memory=[memory])
        await new_agent.load_state(state)

        # Second session
        result2 = await new_agent.run(task="Second task")

        # Verify memory persistence
        assert isinstance(result1.messages[-1], TextMessage)
        assert isinstance(result2.messages[-1], TextMessage)
        assert result1.messages[-1].content == "Response using memory"
        assert result2.messages[-1].content == "Response with updated memory"

        # Verify memory events
        memory_events = [msg for msg in result2.messages if isinstance(msg, MemoryQueryEvent)]
        assert len(memory_events) > 0
        assert any("New memory" in str(event.content) for event in memory_events)