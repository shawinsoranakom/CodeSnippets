def test_agent_and_dsl_default_initialization():
    client = RAGFlow("token", "http://localhost:9380")

    agent = Agent(client, {"id": "agent-1", "title": "Agent One"})
    assert agent.id == "agent-1"
    assert agent.avatar is None
    assert agent.canvas_type is None
    assert agent.description is None
    assert agent.dsl is None

    dsl = Agent.Dsl(client, {})
    assert dsl.answer == []
    assert "begin" in dsl.components
    assert dsl.components["begin"]["obj"]["component_name"] == "Begin"
    assert dsl.graph["nodes"][0]["id"] == "begin"
    assert dsl.history == []
    assert dsl.messages == []
    assert dsl.path == []
    assert dsl.reference == []