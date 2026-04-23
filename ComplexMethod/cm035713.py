def test_load_microagents(temp_microagents_dir):
    """Test loading microagents from directory."""
    repo_agents, knowledge_agents = load_microagents_from_dir(temp_microagents_dir)

    # Check knowledge agents (name derived from filename: knowledge.md -> 'knowledge')
    assert len(knowledge_agents) == 1
    agent_k = knowledge_agents['knowledge']
    assert isinstance(agent_k, KnowledgeMicroagent)
    assert agent_k.type == MicroagentType.KNOWLEDGE  # Check inferred type
    assert 'test' in agent_k.triggers

    # Check repo agents (name derived from filename: repo.md -> 'repo')
    assert len(repo_agents) == 1
    agent_r = repo_agents['repo']
    assert isinstance(agent_r, RepoMicroagent)
    assert agent_r.type == MicroagentType.REPO_KNOWLEDGE