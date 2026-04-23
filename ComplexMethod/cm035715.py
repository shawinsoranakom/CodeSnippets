def test_load_cursorrules_without_microagents_dir(temp_dir_with_cursorrules_only):
    """Test loading .cursorrules file when .openhands/microagents directory doesn't exist.

    This test reproduces the bug where .cursorrules is only loaded when
    .openhands/microagents directory exists.
    """
    # Try to load from non-existent microagents directory
    microagents_dir = temp_dir_with_cursorrules_only / '.openhands' / 'microagents'

    repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)

    # This should find the .cursorrules file even though microagents_dir doesn't exist
    assert len(repo_agents) == 1  # Only .cursorrules
    assert 'cursorrules' in repo_agents
    assert len(knowledge_agents) == 0

    # Check .cursorrules agent
    cursorrules_agent = repo_agents['cursorrules']
    assert isinstance(cursorrules_agent, RepoMicroagent)
    assert cursorrules_agent.name == 'cursorrules'
    assert 'Always use Python for new files' in cursorrules_agent.content
    assert cursorrules_agent.type == MicroagentType.REPO_KNOWLEDGE