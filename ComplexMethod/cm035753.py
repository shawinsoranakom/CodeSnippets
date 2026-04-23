def test_load_from_toml_llm_with_fallback(
    default_config: OpenHandsConfig, generic_llm_toml: str
) -> None:
    """Test that custom LLM configurations fallback non-overridden attributes
    like 'num_retries' from the generic [llm] section.
    """
    load_from_toml(default_config, generic_llm_toml)

    # Verify generic LLM configuration
    generic_llm = default_config.get_llm_config('llm')
    assert generic_llm.model == 'base-model'
    assert generic_llm.api_key.get_secret_value() == 'base-api-key'
    assert generic_llm.num_retries == 3

    # Verify custom1 LLM falls back 'num_retries' from base
    custom1 = default_config.get_llm_config('custom1')
    assert custom1.model == 'custom-model-1'
    assert custom1.api_key.get_secret_value() == 'custom-api-key-1'
    assert custom1.num_retries == 3  # from [llm]

    # Verify custom2 LLM overrides 'num_retries'
    custom2 = default_config.get_llm_config('custom2')
    assert custom2.model == 'custom-model-2'
    assert custom2.api_key.get_secret_value() == 'custom-api-key-2'
    assert custom2.num_retries == 5  # overridden value

    # Verify custom3 LLM inherits all attributes except 'model' and 'api_key'
    custom3 = default_config.get_llm_config('custom3')
    assert custom3.model == 'custom-model-3'
    assert custom3.api_key.get_secret_value() == 'custom-api-key-3'
    assert custom3.num_retries == 3