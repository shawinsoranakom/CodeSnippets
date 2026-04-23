def test_api_keys_repr_str():
    # Test LLMConfig
    llm_config = LLMConfig(
        api_key='my_api_key',
        aws_access_key_id='my_access_key',
        aws_secret_access_key='my_secret_key',
    )

    # Check that no secret keys are emitted in representations of the config object
    assert 'my_api_key' not in repr(llm_config)
    assert 'my_api_key' not in str(llm_config)
    assert 'my_access_key' not in repr(llm_config)
    assert 'my_access_key' not in str(llm_config)
    assert 'my_secret_key' not in repr(llm_config)
    assert 'my_secret_key' not in str(llm_config)

    # Check that no other attrs in LLMConfig have 'key' or 'token' in their name
    # This will fail when new attrs are added, and attract attention
    known_key_token_attrs_llm = [
        'api_key',
        'aws_access_key_id',
        'aws_secret_access_key',
        'input_cost_per_token',
        'output_cost_per_token',
        'custom_tokenizer',
    ]
    for attr_name in LLMConfig.model_fields.keys():
        if (
            not attr_name.startswith('__')
            and attr_name not in known_key_token_attrs_llm
        ):
            assert 'key' not in attr_name.lower(), (
                f"Unexpected attribute '{attr_name}' contains 'key' in LLMConfig"
            )
            assert 'token' not in attr_name.lower() or 'tokens' in attr_name.lower(), (
                f"Unexpected attribute '{attr_name}' contains 'token' in LLMConfig"
            )

    # Test AgentConfig
    # No attrs in AgentConfig have 'key' or 'token' in their name
    agent_config = AgentConfig(enable_prompt_extensions=True, enable_browsing=False)
    for attr_name in AgentConfig.model_fields.keys():
        if not attr_name.startswith('__'):
            assert 'key' not in attr_name.lower(), (
                f"Unexpected attribute '{attr_name}' contains 'key' in AgentConfig"
            )
            assert 'token' not in attr_name.lower() or 'tokens' in attr_name.lower(), (
                f"Unexpected attribute '{attr_name}' contains 'token' in AgentConfig"
            )

    # Test OpenHandsConfig
    app_config = OpenHandsConfig(
        llms={'llm': llm_config},
        agents={'agent': agent_config},
        search_api_key='my_search_api_key',
    )

    assert 'my_search_api_key' not in repr(app_config)
    assert 'my_search_api_key' not in str(app_config)

    # Check that no other attrs in OpenHandsConfig have 'key' or 'token' in their name
    # This will fail when new attrs are added, and attract attention
    known_key_token_attrs_app = [
        'search_api_key',
    ]
    for attr_name in OpenHandsConfig.model_fields.keys():
        if (
            not attr_name.startswith('__')
            and attr_name not in known_key_token_attrs_app
        ):
            assert 'key' not in attr_name.lower(), (
                f"Unexpected attribute '{attr_name}' contains 'key' in OpenHandsConfig"
            )
            assert 'token' not in attr_name.lower() or 'tokens' in attr_name.lower(), (
                f"Unexpected attribute '{attr_name}' contains 'token' in OpenHandsConfig"
            )