def test_condenser_config_from_toml_with_llm_reference(default_config, temp_toml_file):
    """Test loading condenser configuration with LLM reference from TOML."""
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm.condenser_llm]
model = "gpt-4"
api_key = "test-key"

[condenser]
type = "llm"
llm_config = "condenser_llm"
keep_first = 2
max_size = 50
""")

    load_from_toml(default_config, temp_toml_file)

    # Verify that the LLM config was loaded
    assert 'condenser_llm' in default_config.llms
    assert default_config.llms['condenser_llm'].model == 'gpt-4'

    # Verify that the condenser config is correctly assigned to the default agent config
    agent_config = default_config.get_agent_config()
    assert isinstance(agent_config.condenser, LLMSummarizingCondenserConfig)
    assert agent_config.condenser.keep_first == 2
    assert agent_config.condenser.max_size == 50
    assert agent_config.condenser.llm_config.model == 'gpt-4'

    # Test the condenser config with the LLM reference
    from openhands.core.config.condenser_config import (
        condenser_config_from_toml_section,
    )

    condenser_data = {
        'type': 'llm',
        'llm_config': 'condenser_llm',
        'keep_first': 2,
        'max_size': 50,
    }
    condenser_mapping = condenser_config_from_toml_section(
        condenser_data, default_config.llms
    )

    assert 'condenser' in condenser_mapping
    assert isinstance(condenser_mapping['condenser'], LLMSummarizingCondenserConfig)
    assert condenser_mapping['condenser'].keep_first == 2
    assert condenser_mapping['condenser'].max_size == 50
    assert condenser_mapping['condenser'].llm_config.model == 'gpt-4'