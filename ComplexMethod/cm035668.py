def test_protected_fields_not_affected_by_secret_replacement(temp_dir: str):
    """Test that protected system fields are not affected by secret replacement."""
    file_store = get_file_store('local', temp_dir)
    stream = EventStream('test_session', file_store)

    # Set up secrets that might appear in system fields
    stream.set_secrets(
        {
            'secret1': '123',  # Could appear in ID
            'secret2': 'user',  # Could appear in source
            'secret3': 'run',  # Could appear in action/observation
            'secret4': 'Running',  # Could appear in message
        }
    )

    # Create test data with protected fields
    data = {
        'id': 123,
        'timestamp': '2025-07-18T17:01:36.799608',
        'source': 'user',
        'cause': 123,
        'action': 'run',
        'observation': 'run',
        'message': 'Running command: echo hello',
        'content': 'This contains secret1: 123 and secret2: user and secret3: run',
    }

    data_with_secrets_replaced = stream._replace_secrets(data)

    # Protected fields should not be affected at top level
    assert data_with_secrets_replaced['id'] == 123
    assert data_with_secrets_replaced['timestamp'] == '2025-07-18T17:01:36.799608'
    assert data_with_secrets_replaced['source'] == 'user'
    assert data_with_secrets_replaced['cause'] == 123
    assert data_with_secrets_replaced['action'] == 'run'
    assert data_with_secrets_replaced['observation'] == 'run'
    assert data_with_secrets_replaced['message'] == 'Running command: echo hello'

    # But non-protected fields should have secrets replaced
    assert '<secret_hidden>' in data_with_secrets_replaced['content']
    assert '123' not in data_with_secrets_replaced['content']
    assert 'user' not in data_with_secrets_replaced['content']