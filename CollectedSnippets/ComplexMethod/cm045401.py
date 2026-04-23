async def test_digraph_group_chat_resume_with_termination_condition(runtime: AgentRuntime | None) -> None:
    """Test that GraphFlow can be resumed with the same execution state when a termination condition is reached."""
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

    # Create team with MaxMessageTermination that will stop before completion
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        runtime=runtime,
        termination_condition=MaxMessageTermination(3),  # Stop after user + A + B
    )

    # Run the graph flow until termination condition is reached
    result1: TaskResult = await team.run(task="Start execution")

    # Should have stopped at termination condition (user + A + B messages)
    assert len(result1.messages) == 3
    assert result1.messages[0].source == "user"
    assert result1.messages[1].source == "A"
    assert result1.messages[2].source == "B"
    assert result1.stop_reason is not None

    # Verify A and B ran, but C did not
    assert agent_a.total_messages == 1
    assert agent_b.total_messages == 1
    assert agent_c.total_messages == 0

    # Resume the graph flow with no task to continue where it left off
    result2: TaskResult = await team.run()

    # Should continue and execute C, then complete without stop agent message
    assert len(result2.messages) == 1
    assert result2.messages[0].source == "C"
    assert result2.stop_reason is not None

    # Verify C now ran and the execution state was preserved
    assert agent_a.total_messages == 1  # Still only ran once
    assert agent_b.total_messages == 1  # Still only ran once
    assert agent_c.total_messages == 1