def test_microagent_observation_knowledge_microagent_serialization():
    """Test serialization of a RecallObservation with KNOWLEDGE_MICROAGENT type."""
    # Create a RecallObservation with microagent knowledge content
    original = RecallObservation(
        content='Knowledge microagent information',
        recall_type=RecallType.KNOWLEDGE,
        repo_branch='',
        microagent_knowledge=[
            MicroagentKnowledge(
                name='python_best_practices',
                trigger='python',
                content='Always use virtual environments for Python projects.',
            ),
            MicroagentKnowledge(
                name='git_workflow',
                trigger='git',
                content='Create a new branch for each feature or bugfix.',
            ),
        ],
    )

    # Serialize to dictionary
    serialized = event_to_dict(original)

    # Verify serialized data structure
    assert serialized['observation'] == ObservationType.RECALL
    assert serialized['content'] == 'Knowledge microagent information'
    assert serialized['extras']['recall_type'] == RecallType.KNOWLEDGE.value
    assert len(serialized['extras']['microagent_knowledge']) == 2
    assert serialized['extras']['microagent_knowledge'][0]['trigger'] == 'python'

    # Deserialize back to RecallObservation
    deserialized = observation_from_dict(serialized)

    # Verify properties are preserved
    assert deserialized.recall_type == RecallType.KNOWLEDGE
    assert deserialized.microagent_knowledge == original.microagent_knowledge
    assert deserialized.content == original.content

    # Check that environment info fields are empty
    assert deserialized.repo_name == ''
    assert deserialized.repo_directory == ''
    assert deserialized.repo_instructions == ''
    assert deserialized.runtime_hosts == {}