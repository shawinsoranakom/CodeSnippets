async def test_digraph_group_chat_multiple_task_execution(runtime: AgentRuntime | None) -> None:
    """Test that GraphFlow can run multiple tasks sequentially after resetting execution state."""
    # Create agents A → B → C
    agent_a = _EchoAgent("A", description="Echo agent A")
    agent_b = _EchoAgent("B", description="Echo agent B")
    agent_c = _EchoAgent("C", description="Echo agent C")

    # Define graph A → B → C
    graph = DiGraph(
        nodes={
            "A": DiGraphNode(name="A", edges=[DiGraphEdge(target="B")]),
            "B": DiGraphNode(name="B", edges=[DiGraphEdge(target="C")]),
            "C": DiGraphNode(name="C", edges=[]),
        }
    )

    # Create team using Graph
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        runtime=runtime,
        termination_condition=MaxMessageTermination(5),
    )

    # Run the first task
    result1: TaskResult = await team.run(task="First task")

    assert len(result1.messages) == 4
    assert isinstance(result1.messages[0], TextMessage)
    assert result1.messages[0].source == "user"
    assert result1.messages[0].content == "First task"
    assert result1.messages[1].source == "A"
    assert result1.messages[2].source == "B"
    assert result1.messages[3].source == "C"
    assert result1.stop_reason is not None

    # Run the second task - should work without explicit reset
    result2: TaskResult = await team.run(task="Second task")

    assert len(result2.messages) == 4
    assert isinstance(result2.messages[0], TextMessage)
    assert result2.messages[0].source == "user"
    assert result2.messages[0].content == "Second task"
    assert result2.messages[1].source == "A"
    assert result2.messages[2].source == "B"
    assert result2.messages[3].source == "C"
    assert result2.stop_reason is not None

    # Verify agents were properly reset and executed again
    assert agent_a.total_messages == 2  # Once for each task
    assert agent_b.total_messages == 2  # Once for each task
    assert agent_c.total_messages == 2