def test_microagent_observation_environment_serialization():
    """Test serialization of a RecallObservation with ENVIRONMENT type."""
    # Create a RecallObservation with environment info
    original = RecallObservation(
        content='Environment information',
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='OpenHands',
        repo_directory='/workspace/openhands',
        repo_branch='main',
        repo_instructions="Follow the project's coding style guide.",
        runtime_hosts={'127.0.0.1': 8080, 'localhost': 5000},
        additional_agent_instructions='You know it all about this runtime',
    )

    # Serialize to dictionary
    serialized = event_to_dict(original)

    # Verify serialized data structure
    assert serialized['observation'] == ObservationType.RECALL
    assert serialized['content'] == 'Environment information'
    assert serialized['extras']['recall_type'] == RecallType.WORKSPACE_CONTEXT.value
    assert serialized['extras']['repo_name'] == 'OpenHands'
    assert serialized['extras']['runtime_hosts'] == {
        '127.0.0.1': 8080,
        'localhost': 5000,
    }
    assert (
        serialized['extras']['additional_agent_instructions']
        == 'You know it all about this runtime'
    )
    # Deserialize back to RecallObservation
    deserialized = observation_from_dict(serialized)

    # Verify properties are preserved
    assert deserialized.recall_type == RecallType.WORKSPACE_CONTEXT
    assert deserialized.repo_name == original.repo_name
    assert deserialized.repo_directory == original.repo_directory
    assert deserialized.repo_instructions == original.repo_instructions
    assert deserialized.runtime_hosts == original.runtime_hosts
    assert (
        deserialized.additional_agent_instructions
        == original.additional_agent_instructions
    )
    # Check that knowledge microagent fields are empty
    assert deserialized.microagent_knowledge == []