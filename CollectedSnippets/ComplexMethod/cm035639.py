def test_gemini_performance_optimization_end_to_end(mock_completion):
    """Test the complete Gemini performance optimization flow end-to-end."""
    # Mock the completion response
    mock_completion.return_value = {
        'choices': [{'message': {'content': 'Optimized response'}}],
        'usage': {'prompt_tokens': 50, 'completion_tokens': 25},
    }

    # Create Gemini configuration
    config = LLMConfig(model='gemini-2.5-pro', api_key='test_key')

    # Verify config has optimized defaults
    assert config.reasoning_effort is None

    # Create LLM and make completion
    llm = LLM(config, service_id='test-service')
    messages = [{'role': 'user', 'content': 'Solve this complex problem'}]

    response = llm.completion(messages=messages)

    # Verify response was generated
    assert response['choices'][0]['message']['content'] == 'Optimized response'

    # Verify optimization parameters were applied
    call_kwargs = mock_completion.call_args[1]
    assert 'thinking' in call_kwargs
    assert call_kwargs['thinking'] == {'budget_tokens': 128}
    assert call_kwargs.get('reasoning_effort') is None

    # Verify temperature and top_p were removed for reasoning models
    assert 'temperature' not in call_kwargs
    assert 'top_p' not in call_kwargs