def test_user_microagents_loading(temp_user_microagents_dir):
    """Test that user microagents are loaded from ~/.openhands/microagents/."""
    with patch(
        'openhands.memory.memory.USER_MICROAGENTS_DIR', str(temp_user_microagents_dir)
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create event stream and memory
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)
            memory = Memory(event_stream, 'test_sid')

            # Check that user microagents were loaded
            assert 'user_knowledge' in memory.knowledge_microagents
            assert 'user_repo' in memory.repo_microagents

            # Verify the loaded agents
            user_knowledge = memory.knowledge_microagents['user_knowledge']
            assert isinstance(user_knowledge, KnowledgeMicroagent)
            assert user_knowledge.type == MicroagentType.KNOWLEDGE
            assert 'user-test' in user_knowledge.triggers
            assert 'personal' in user_knowledge.triggers

            user_repo = memory.repo_microagents['user_repo']
            assert isinstance(user_repo, RepoMicroagent)
            assert user_repo.type == MicroagentType.REPO_KNOWLEDGE