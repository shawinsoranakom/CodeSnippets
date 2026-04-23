async def test_message_filter_agent_loop_graph_visibility(runtime: AgentRuntime | None) -> None:
    agent_a_inner = _TestMessageFilterAgent("A")
    agent_a = MessageFilterAgent(
        name="A",
        wrapped_agent=agent_a_inner,
        filter=MessageFilterConfig(
            per_source=[
                PerSourceFilter(source="user", position="first", count=1),
                PerSourceFilter(source="B", position="last", count=1),
            ]
        ),
    )

    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.replay import ReplayChatCompletionClient

    model_client = ReplayChatCompletionClient(["loop", "loop", "exit"])
    agent_b_inner = AssistantAgent("B", model_client=model_client)
    agent_b = MessageFilterAgent(
        name="B",
        wrapped_agent=agent_b_inner,
        filter=MessageFilterConfig(
            per_source=[
                PerSourceFilter(source="user", position="first", count=1),
                PerSourceFilter(source="A", position="last", count=1),
                PerSourceFilter(source="B", position="last", count=10),
            ]
        ),
    )

    agent_c_inner = _TestMessageFilterAgent("C")
    agent_c = MessageFilterAgent(
        name="C",
        wrapped_agent=agent_c_inner,
        filter=MessageFilterConfig(
            per_source=[
                PerSourceFilter(source="user", position="first", count=1),
                PerSourceFilter(source="B", position="last", count=1),
            ]
        ),
    )

    graph = DiGraph(
        nodes={
            "A": DiGraphNode(name="A", edges=[DiGraphEdge(target="B")]),
            "B": DiGraphNode(
                name="B",
                edges=[
                    DiGraphEdge(target="C", condition="exit"),
                    DiGraphEdge(target="A", condition="loop"),
                ],
            ),
            "C": DiGraphNode(name="C", edges=[]),
        },
        default_start_node="A",
    )

    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        runtime=runtime,
        termination_condition=MaxMessageTermination(20),
    )

    result = await team.run(task="Start")
    assert result.stop_reason is not None

    # Check A received: 1 user + 2 from B
    assert [m.source for m in agent_a_inner.received_messages].count("user") == 1
    assert [m.source for m in agent_a_inner.received_messages].count("B") == 2

    # Check C received: 1 user + 1 from B
    assert [m.source for m in agent_c_inner.received_messages].count("user") == 1
    assert [m.source for m in agent_c_inner.received_messages].count("B") == 1

    # Check B received: 1 user + multiple from A + own messages
    model_msgs = await agent_b_inner.model_context.get_messages()
    sources = [m.source for m in model_msgs]  # type: ignore[union-attr]
    assert sources.count("user") == 1  # pyright: ignore[reportUnknownMemberType]
    assert sources.count("A") >= 3  # pyright: ignore[reportUnknownMemberType]
    assert sources.count("B") >= 2