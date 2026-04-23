def test_load_both_cursorrules_and_agents_md(temp_dir_with_both_cursorrules_and_agents):
    """Test loading both .cursorrules and AGENTS.md files when .openhands/microagents doesn't exist."""
    # Try to load from non-existent microagents directory
    microagents_dir = (
        temp_dir_with_both_cursorrules_and_agents / '.openhands' / 'microagents'
    )

    repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)

    # This should find both files
    assert len(repo_agents) == 2  # .cursorrules + AGENTS.md
    assert 'cursorrules' in repo_agents
    assert 'agents' in repo_agents
    assert len(knowledge_agents) == 0

    # Check both agents
    cursorrules_agent = repo_agents['cursorrules']
    assert isinstance(cursorrules_agent, RepoMicroagent)
    assert 'Always use Python for new files' in cursorrules_agent.content

    agents_agent = repo_agents['agents']
    assert isinstance(agents_agent, RepoMicroagent)
    assert 'Install deps: `poetry install`' in agents_agent.content