def test_llm_token_usage(mock_litellm_completion, default_config):
    # This mock response includes usage details with prompt_tokens,
    # completion_tokens, prompt_tokens_details.cached_tokens, and model_extra.cache_creation_input_tokens
    mock_response_1 = {
        'id': 'test-response-usage',
        'choices': [{'message': {'content': 'Usage test response'}}],
        'usage': {
            'prompt_tokens': 12,
            'completion_tokens': 3,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=2),
            'model_extra': {'cache_creation_input_tokens': 5},
        },
    }

    # Create a second usage scenario to test accumulation and a different response_id
    mock_response_2 = {
        'id': 'test-response-usage-2',
        'choices': [{'message': {'content': 'Second usage test response'}}],
        'usage': {
            'prompt_tokens': 7,
            'completion_tokens': 2,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=1),
            'model_extra': {'cache_creation_input_tokens': 3},
        },
    }

    # We'll make mock_litellm_completion return these responses in sequence
    mock_litellm_completion.side_effect = [mock_response_1, mock_response_2]

    llm = LLM(config=default_config, service_id='test-service')

    # First call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello usage!'}])

    # Verify we have exactly one usage record after first call
    token_usage_list = llm.metrics.get()['token_usages']
    assert len(token_usage_list) == 1
    usage_entry_1 = token_usage_list[0]
    assert usage_entry_1['prompt_tokens'] == 12
    assert usage_entry_1['completion_tokens'] == 3
    assert usage_entry_1['cache_read_tokens'] == 2
    assert usage_entry_1['cache_write_tokens'] == 5
    assert usage_entry_1['response_id'] == 'test-response-usage'

    # Second call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello again!'}])

    # Now we expect two usage records total
    token_usage_list = llm.metrics.get()['token_usages']
    assert len(token_usage_list) == 2
    usage_entry_2 = token_usage_list[-1]
    assert usage_entry_2['prompt_tokens'] == 7
    assert usage_entry_2['completion_tokens'] == 2
    assert usage_entry_2['cache_read_tokens'] == 1
    assert usage_entry_2['cache_write_tokens'] == 3
    assert usage_entry_2['response_id'] == 'test-response-usage-2'