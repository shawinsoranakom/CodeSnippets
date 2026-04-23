def test_condenser_config_from_toml_basic(default_config, temp_toml_file):
    """Test loading basic condenser configuration from TOML."""
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[condenser]
type = "recent"
keep_first = 3
max_events = 15
""")

    load_from_toml(default_config, temp_toml_file)

    # Verify that the condenser config is correctly assigned to the default agent config
    agent_config = default_config.get_agent_config()
    assert isinstance(agent_config.condenser, RecentEventsCondenserConfig)
    assert agent_config.condenser.keep_first == 3
    assert agent_config.condenser.max_events == 15

    # We can also verify the function works directly
    from openhands.core.config.condenser_config import (
        condenser_config_from_toml_section,
    )

    condenser_data = {'type': 'recent', 'keep_first': 3, 'max_events': 15}
    condenser_mapping = condenser_config_from_toml_section(condenser_data)

    assert 'condenser' in condenser_mapping
    assert isinstance(condenser_mapping['condenser'], RecentEventsCondenserConfig)
    assert condenser_mapping['condenser'].keep_first == 3
    assert condenser_mapping['condenser'].max_events == 15