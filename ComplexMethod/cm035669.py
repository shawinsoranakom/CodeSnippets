def test_nested_dict_secret_replacement(temp_dir: str):
    """Test that secrets are replaced in nested dictionaries while preserving protected fields."""
    file_store = get_file_store('local', temp_dir)
    stream = EventStream('test_session', file_store)

    stream.set_secrets({'secret': 'password123'})

    # Create nested data structure
    data = {
        'timestamp': '2025-07-18T17:01:36.799608',
        'args': {
            'command': 'login --password password123',
            'env': {
                'SECRET_KEY': 'password123',
                'timestamp': 'password123_timestamp',  # This should be replaced since it's not top-level
            },
        },
    }

    data_with_secrets_replaced = stream._replace_secrets(data)

    # Top-level timestamp should be protected
    assert data_with_secrets_replaced['timestamp'] == '2025-07-18T17:01:36.799608'

    # Nested secrets should be replaced
    assert '<secret_hidden>' in data_with_secrets_replaced['args']['command']
    assert data_with_secrets_replaced['args']['env']['SECRET_KEY'] == '<secret_hidden>'
    assert '<secret_hidden>' in data_with_secrets_replaced['args']['env']['timestamp']

    # Original secret should not appear in nested content
    assert 'password123' not in data_with_secrets_replaced['args']['command']
    assert 'password123' not in data_with_secrets_replaced['args']['env']['SECRET_KEY']
    assert 'password123' not in data_with_secrets_replaced['args']['env']['timestamp']