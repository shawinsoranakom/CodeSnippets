async def test_agent_async_iterator_output_structure() -> None:
    """Test the async output structure of AgentExecutorIterator."""
    agent = _get_agent()
    agent_async_iter = agent.iter(inputs="when was langchain made", async_=True)

    assert isinstance(agent_async_iter, AgentExecutorIterator)
    async for step in agent_async_iter:
        assert isinstance(step, dict)
        if "intermediate_step" in step:
            assert isinstance(step["intermediate_step"], list)
        elif "output" in step:
            assert isinstance(step["output"], str)
        else:
            pytest.fail("Unexpected output structure")