async def test_selector_group_chat_custom_selector(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(["agent3"])
    agent1 = _EchoAgent("agent1", description="echo agent 1")
    agent2 = _EchoAgent("agent2", description="echo agent 2")
    agent3 = _EchoAgent("agent3", description="echo agent 3")
    agent4 = _EchoAgent("agent4", description="echo agent 4")

    def _select_agent(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
        if len(messages) == 0:
            return "agent1"
        elif messages[-1].source == "agent1":
            return "agent2"
        elif messages[-1].source == "agent2":
            return None
        elif messages[-1].source == "agent3":
            return "agent4"
        else:
            return "agent1"

    termination = MaxMessageTermination(6)
    team = SelectorGroupChat(
        participants=[agent1, agent2, agent3, agent4],
        model_client=model_client,
        selector_func=_select_agent,
        termination_condition=termination,
        runtime=runtime,
    )
    result = await team.run(task="task")
    assert len(result.messages) == 6
    assert result.messages[1].source == "agent1"
    assert result.messages[2].source == "agent2"
    assert result.messages[3].source == "agent3"
    assert result.messages[4].source == "agent4"
    assert result.messages[5].source == "agent1"
    assert (
        result.stop_reason is not None
        and result.stop_reason == "Maximum number of messages 6 reached, current message count: 6"
    )