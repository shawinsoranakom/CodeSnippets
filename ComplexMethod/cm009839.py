def test_agent_iterator_properties_and_setters() -> None:
    """Test properties and setters of AgentExecutorIterator."""
    agent = _get_agent()
    agent.tags = None
    agent_iter = agent.iter(inputs="when was langchain made")

    assert isinstance(agent_iter, AgentExecutorIterator)
    assert isinstance(agent_iter.inputs, dict)
    assert agent_iter.callbacks is None
    assert agent_iter.tags is None
    assert isinstance(agent_iter.agent_executor, AgentExecutor)

    agent_iter.inputs = "New input"
    assert isinstance(agent_iter.inputs, dict)

    agent_iter.callbacks = [FakeCallbackHandler()]
    assert isinstance(agent_iter.callbacks, list)

    agent_iter.tags = ["test"]
    assert isinstance(agent_iter.tags, list)

    new_agent = _get_agent()
    agent_iter.agent_executor = new_agent
    assert isinstance(agent_iter.agent_executor, AgentExecutor)