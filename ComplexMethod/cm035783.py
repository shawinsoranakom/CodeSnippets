def test_load_microagents_with_selected_repo(temp_dir, runtime_cls, run_as_openhands):
    """Test loading microagents from a selected repository."""
    # Create test files in a repository-like structure
    repo_dir = Path(temp_dir) / 'OpenHands'
    repo_dir.mkdir(parents=True)
    _create_test_microagents(str(repo_dir))

    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents with selected repository
        loaded_agents = runtime.get_microagents_from_selected_repo(
            'OpenHands/OpenHands'
        )

        # Verify all agents are loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroagent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroagent)]

        # Check knowledge agents
        assert len(knowledge_agents) == 1
        agent = knowledge_agents[0]
        assert agent.name == 'knowledge/knowledge'
        assert 'test' in agent.triggers
        assert 'pytest' in agent.triggers

        # Check repo agents (including legacy)
        assert len(repo_agents) == 2  # repo.md + .openhands_instructions
        repo_names = {a.name for a in repo_agents}
        assert 'repo' in repo_names
        assert 'repo_legacy' in repo_names

    finally:
        _close_test_runtime(runtime)