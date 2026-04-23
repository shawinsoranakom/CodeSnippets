def test_featurizer_user_message(featurizer):
    """Test user_message method."""
    # With cache
    message = featurizer.user_message('Test issue', set_cache=True)
    assert message['role'] == 'user'
    assert message['content'] == 'Test message prefix: Test issue'
    assert 'cache_control' in message
    assert message['cache_control']['type'] == 'ephemeral'

    # Without cache
    message = featurizer.user_message('Test issue', set_cache=False)
    assert message['role'] == 'user'
    assert message['content'] == 'Test message prefix: Test issue'
    assert 'cache_control' not in message