async def test_routed_agent_message_matching() -> None:
    runtime = SingleThreadedAgentRuntime()
    await RoutedAgentMessageCustomMatch.register(runtime, "message_match", RoutedAgentMessageCustomMatch)
    agent_id = AgentId(type="message_match", key="default")

    agent = await runtime.try_get_underlying_agent_instance(agent_id, type=RoutedAgentMessageCustomMatch)
    assert agent is not None
    assert agent.handler_one_called is False
    assert agent.handler_two_called is False

    runtime.start()
    await runtime.send_message(MyMessage("one"), recipient=agent_id)
    await runtime.stop_when_idle()
    agent = await runtime.try_get_underlying_agent_instance(agent_id, type=RoutedAgentMessageCustomMatch)
    assert agent.handler_one_called is True
    assert agent.handler_two_called is False

    runtime.start()
    await runtime.send_message(MyMessage("two"), recipient=agent_id)
    await runtime.stop_when_idle()
    agent = await runtime.try_get_underlying_agent_instance(agent_id, type=RoutedAgentMessageCustomMatch)
    assert agent.handler_one_called is True
    assert agent.handler_two_called is True