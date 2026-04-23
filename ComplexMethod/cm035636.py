def test_response_latency_tracking(mock_time, mock_litellm_completion):
    # Mock time.time() to return controlled values
    mock_time.side_effect = [1000.0, 1002.5]  # Start time, end time (2.5s difference)

    # Mock the completion response with a specific ID
    mock_response = {
        'id': 'test-response-123',
        'choices': [{'message': {'content': 'Test response'}}],
    }
    mock_litellm_completion.return_value = mock_response

    # Create LLM instance and make a completion call
    config = LLMConfig(model='gpt-4o', api_key='test_key')
    llm = LLM(config, service_id='test-service')
    response = llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify the response latency was tracked correctly
    assert len(llm.metrics.response_latencies) == 1
    latency_record = llm.metrics.response_latencies[0]
    assert latency_record.model == 'gpt-4o'
    assert (
        latency_record.latency == 2.5
    )  # Should be the difference between our mocked times
    assert latency_record.response_id == 'test-response-123'

    # Verify the completion response was returned correctly
    assert response['id'] == 'test-response-123'
    assert response['choices'][0]['message']['content'] == 'Test response'

    # To make sure the metrics fail gracefully, set the start/end time to go backwards.
    mock_time.side_effect = [1000.0, 999.0]
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # There should now be 2 latencies, the last of which has the value clipped to 0
    assert len(llm.metrics.response_latencies) == 2
    latency_record = llm.metrics.response_latencies[-1]
    assert latency_record.latency == 0.0