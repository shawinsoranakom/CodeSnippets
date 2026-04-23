def test_metrics_merge_accumulated_token_usage():
    """Test that accumulated token usage is properly merged between two Metrics instances."""
    # Create two Metrics instances
    metrics1 = Metrics(model_name='model1')
    metrics2 = Metrics(model_name='model2')

    # Add token usage to each
    metrics1.add_token_usage(10, 5, 3, 2, 1000, 'response-1')
    metrics2.add_token_usage(8, 6, 2, 4, 1000, 'response-2')

    # Verify initial accumulated token usage
    metrics1_data = metrics1.get()
    accumulated1 = metrics1_data['accumulated_token_usage']
    assert accumulated1['prompt_tokens'] == 10
    assert accumulated1['completion_tokens'] == 5
    assert accumulated1['cache_read_tokens'] == 3
    assert accumulated1['cache_write_tokens'] == 2

    metrics2_data = metrics2.get()
    accumulated2 = metrics2_data['accumulated_token_usage']
    assert accumulated2['prompt_tokens'] == 8
    assert accumulated2['completion_tokens'] == 6
    assert accumulated2['cache_read_tokens'] == 2
    assert accumulated2['cache_write_tokens'] == 4

    # Merge metrics2 into metrics1
    metrics1.merge(metrics2)

    # Verify merged accumulated token usage
    merged_data = metrics1.get()
    merged_accumulated = merged_data['accumulated_token_usage']
    assert merged_accumulated['prompt_tokens'] == 18  # 10 + 8
    assert merged_accumulated['completion_tokens'] == 11  # 5 + 6
    assert merged_accumulated['cache_read_tokens'] == 5  # 3 + 2
    assert merged_accumulated['cache_write_tokens'] == 6  # 2 + 4

    # Verify individual token usage records are maintained
    token_usages = merged_data['token_usages']
    assert len(token_usages) == 2
    assert token_usages[0]['response_id'] == 'response-1'
    assert token_usages[1]['response_id'] == 'response-2'