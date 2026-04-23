def test_agent_iterator_reset() -> None:
    """Test reset functionality of AgentExecutorIterator."""
    agent = _get_agent()
    agent_iter = agent.iter(inputs="when was langchain made")
    assert isinstance(agent_iter, AgentExecutorIterator)

    # Perform one iteration
    iterator = iter(agent_iter)
    next(iterator)

    # Check if properties are updated
    assert agent_iter.iterations == 1
    assert agent_iter.time_elapsed > 0.0
    assert agent_iter.intermediate_steps

    # Reset the iterator
    agent_iter.reset()

    # Check if properties are reset
    assert agent_iter.iterations == 0
    assert agent_iter.time_elapsed == 0.0
    assert not agent_iter.intermediate_steps