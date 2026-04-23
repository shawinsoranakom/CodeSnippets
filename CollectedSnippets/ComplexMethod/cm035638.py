def test_accumulated_token_usage(mock_litellm_completion, default_config):
    """Test that token usage is properly accumulated across multiple LLM calls."""
    # Mock responses with token usage information
    mock_response_1 = {
        'id': 'test-response-1',
        'choices': [{'message': {'content': 'First response'}}],
        'usage': {
            'prompt_tokens': 10,
            'completion_tokens': 5,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=3),
            'model_extra': {'cache_creation_input_tokens': 4},
        },
    }

    mock_response_2 = {
        'id': 'test-response-2',
        'choices': [{'message': {'content': 'Second response'}}],
        'usage': {
            'prompt_tokens': 8,
            'completion_tokens': 6,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=2),
            'model_extra': {'cache_creation_input_tokens': 3},
        },
    }

    # Set up the mock to return these responses in sequence
    mock_litellm_completion.side_effect = [mock_response_1, mock_response_2]

    # Create LLM instance
    llm = LLM(config=default_config, service_id='test-service')

    # First call
    llm.completion(messages=[{'role': 'user', 'content': 'First message'}])

    # Check accumulated token usage after first call
    metrics_data = llm.metrics.get()
    accumulated_usage = metrics_data['accumulated_token_usage']

    assert accumulated_usage['prompt_tokens'] == 10
    assert accumulated_usage['completion_tokens'] == 5
    assert accumulated_usage['cache_read_tokens'] == 3
    assert accumulated_usage['cache_write_tokens'] == 4

    # Second call
    llm.completion(messages=[{'role': 'user', 'content': 'Second message'}])

    # Check accumulated token usage after second call
    metrics_data = llm.metrics.get()
    accumulated_usage = metrics_data['accumulated_token_usage']

    # Values should be the sum of both calls
    assert accumulated_usage['prompt_tokens'] == 18  # 10 + 8
    assert accumulated_usage['completion_tokens'] == 11  # 5 + 6
    assert accumulated_usage['cache_read_tokens'] == 5  # 3 + 2
    assert accumulated_usage['cache_write_tokens'] == 7  # 4 + 3

    # Verify individual token usage records are still maintained
    token_usages = metrics_data['token_usages']
    assert len(token_usages) == 2

    # First record
    assert token_usages[0]['prompt_tokens'] == 10
    assert token_usages[0]['completion_tokens'] == 5
    assert token_usages[0]['cache_read_tokens'] == 3
    assert token_usages[0]['cache_write_tokens'] == 4
    assert token_usages[0]['response_id'] == 'test-response-1'

    # Second record
    assert token_usages[1]['prompt_tokens'] == 8
    assert token_usages[1]['completion_tokens'] == 6
    assert token_usages[1]['cache_read_tokens'] == 2
    assert token_usages[1]['cache_write_tokens'] == 3
    assert token_usages[1]['response_id'] == 'test-response-2'