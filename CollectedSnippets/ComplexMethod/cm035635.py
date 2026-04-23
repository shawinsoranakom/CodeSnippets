def test_llm_init_with_custom_config():
    custom_config = LLMConfig(
        model='custom-model',
        api_key='custom_key',
        max_input_tokens=5000,
        max_output_tokens=1500,
        temperature=0.8,
        top_p=0.9,
        top_k=None,
    )
    llm = LLM(custom_config, service_id='test-service')
    assert llm.config.model == 'custom-model'
    assert llm.config.api_key.get_secret_value() == 'custom_key'
    assert llm.config.max_input_tokens == 5000
    assert llm.config.max_output_tokens == 1500
    assert llm.config.temperature == 0.8
    assert llm.config.top_p == 0.9
    assert llm.config.top_k is None