def test_microagent_observation_combined_serialization():
    """Test serialization of a RecallObservation with both types of information."""
    # Create a RecallObservation with both environment and microagent info
    # Note: In practice, recall_type would still be one specific type,
    # but the object could contain both types of fields
    original = RecallObservation(
        content='Combined information',
        recall_type=RecallType.WORKSPACE_CONTEXT,
        # Environment info
        repo_name='OpenHands',
        repo_directory='/workspace/openhands',
        repo_branch='main',
        repo_instructions="Follow the project's coding style guide.",
        runtime_hosts={'127.0.0.1': 8080},
        additional_agent_instructions='You know it all about this runtime',
        # Knowledge microagent info
        microagent_knowledge=[
            MicroagentKnowledge(
                name='python_best_practices',
                trigger='python',
                content='Always use virtual environments for Python projects.',
            ),
        ],
    )

    # Serialize to dictionary
    serialized = event_to_dict(original)

    # Verify serialized data has both types of fields
    assert serialized['extras']['recall_type'] == RecallType.WORKSPACE_CONTEXT.value
    assert serialized['extras']['repo_name'] == 'OpenHands'
    assert (
        serialized['extras']['microagent_knowledge'][0]['name']
        == 'python_best_practices'
    )
    assert (
        serialized['extras']['additional_agent_instructions']
        == 'You know it all about this runtime'
    )
    # Deserialize back to RecallObservation
    deserialized = observation_from_dict(serialized)

    # Verify all properties are preserved
    assert deserialized.recall_type == RecallType.WORKSPACE_CONTEXT

    # Environment properties
    assert deserialized.repo_name == original.repo_name
    assert deserialized.repo_directory == original.repo_directory
    assert deserialized.repo_instructions == original.repo_instructions
    assert deserialized.runtime_hosts == original.runtime_hosts
    assert (
        deserialized.additional_agent_instructions
        == original.additional_agent_instructions
    )

    # Knowledge microagent properties
    assert deserialized.microagent_knowledge == original.microagent_knowledge