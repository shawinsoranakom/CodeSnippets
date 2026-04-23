def test_load_microagents_with_missing_files(temp_dir, runtime_cls, run_as_openhands):
    """Test loading microagents when some files are missing."""
    # Create only repo.md, no other files
    microagents_dir = Path(temp_dir) / '.openhands' / 'microagents'
    microagents_dir.mkdir(parents=True, exist_ok=True)

    repo_agent = """---
name: test_repo_agent
type: repo
version: 1.0.0
agent: CodeActAgent
---

# Test Repository Agent

Repository-specific test instructions.
"""
    (microagents_dir / 'repo.md').write_text(repo_agent)

    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents
        loaded_agents = runtime.get_microagents_from_selected_repo(None)

        # Verify only repo agent is loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroagent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroagent)]

        assert len(knowledge_agents) == 0
        assert len(repo_agents) == 1

        agent = repo_agents[0]
        assert agent.name == 'repo'

    finally:
        _close_test_runtime(runtime)