def test_agent_config_from_toml_section():
    """Test that AgentConfig.from_toml_section correctly parses agent configurations from TOML."""
    from openhands.core.config.agent_config import AgentConfig

    # Test with base config and custom configs
    agent_section = {
        'enable_prompt_extensions': True,
        'enable_browsing': True,
        'CustomAgent1': {'enable_browsing': False},
        'CustomAgent2': {'enable_prompt_extensions': False},
        'InvalidAgent': {
            'invalid_field': 'some_value'  # This should be skipped but not affect others
        },
    }

    # Parse the section
    result = AgentConfig.from_toml_section(agent_section)

    # Verify the base config was correctly parsed
    assert 'agent' in result
    assert result['agent'].enable_prompt_extensions is True
    assert result['agent'].enable_browsing is True

    # Verify custom configs were correctly parsed and inherit from base
    assert 'CustomAgent1' in result
    assert result['CustomAgent1'].enable_browsing is False  # Overridden
    assert result['CustomAgent1'].enable_prompt_extensions is True  # Inherited

    assert 'CustomAgent2' in result
    assert result['CustomAgent2'].enable_browsing is True  # Inherited
    assert result['CustomAgent2'].enable_prompt_extensions is False  # Overridden

    # Verify the invalid config was skipped
    assert 'InvalidAgent' not in result