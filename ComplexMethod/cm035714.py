def test_load_microagents_with_cursorrules(temp_microagents_dir_with_cursorrules):
    """Test loading microagents when .cursorrules file exists."""
    microagents_dir = (
        temp_microagents_dir_with_cursorrules / '.openhands' / 'microagents'
    )

    repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)

    # Verify that .cursorrules file was loaded as a RepoMicroagent
    assert len(repo_agents) == 2  # repo.md + .cursorrules
    assert 'repo' in repo_agents
    assert 'cursorrules' in repo_agents

    # Check .cursorrules agent
    cursorrules_agent = repo_agents['cursorrules']
    assert isinstance(cursorrules_agent, RepoMicroagent)
    assert cursorrules_agent.name == 'cursorrules'
    assert 'Always use TypeScript for new files' in cursorrules_agent.content
    assert cursorrules_agent.type == MicroagentType.REPO_KNOWLEDGE