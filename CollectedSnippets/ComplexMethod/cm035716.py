def test_load_agents_md_without_microagents_dir(temp_dir_with_agents_md_only):
    """Test loading AGENTS.md file when .openhands/microagents directory doesn't exist."""
    # Try to load from non-existent microagents directory
    microagents_dir = temp_dir_with_agents_md_only / '.openhands' / 'microagents'

    repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)

    # This should find the AGENTS.md file even though microagents_dir doesn't exist
    assert len(repo_agents) == 1  # Only AGENTS.md
    assert 'agents' in repo_agents
    assert len(knowledge_agents) == 0

    # Check AGENTS.md agent
    agents_agent = repo_agents['agents']
    assert isinstance(agents_agent, RepoMicroagent)
    assert agents_agent.name == 'agents'
    assert 'Install deps: `poetry install`' in agents_agent.content
    assert agents_agent.type == MicroagentType.REPO_KNOWLEDGE