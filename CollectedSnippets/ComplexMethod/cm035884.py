async def test_gitlab_events_deduplication_without_object_id(
    mock_sio, mock_gitlab_manager, mock_verify_signature
):
    """Test that GitLab events without object_attributes.id are deduplicated using hash of payload."""
    # Setup mocks
    mock_verify_signature.return_value = None
    mock_gitlab_manager.receive_message = AsyncMock()

    # Mock Redis
    mock_redis = AsyncMock()
    mock_sio.manager.redis = mock_redis

    # First request - Redis returns True (key was set)
    mock_redis.set.return_value = True

    # Create a mock request with a payload without object_attributes.id
    payload = {
        'object_kind': 'pipeline',
        'object_attributes': {
            'ref': 'main',
            'status': 'success',
            # No 'id' field
        },
    }

    mock_request = MagicMock()
    mock_request.json = AsyncMock(return_value=payload)

    # Calculate the expected hash
    dedup_json = json.dumps(payload, sort_keys=True)
    expected_hash = hashlib.sha256(dedup_json.encode()).hexdigest()
    expected_key = f'gitlab_msg: {expected_hash}'  # Note the space after 'gitlab_msg:'

    # Call the endpoint
    response = await gitlab_events(
        request=mock_request,
        x_gitlab_token='test_token',
        x_openhands_webhook_id='test_webhook_id',
        x_openhands_user_id='test_user_id',
    )

    # Verify Redis was called to set the key with the hash
    mock_redis.set.assert_called_once_with(expected_key, 1, nx=True, ex=60)

    # Verify the message was processed
    assert mock_gitlab_manager.receive_message.called
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    # Reset mocks
    mock_redis.set.reset_mock()
    mock_gitlab_manager.receive_message.reset_mock()

    # Second request - Redis returns False (key already exists)
    mock_redis.set.return_value = False

    # Call the endpoint again with the same payload
    response = await gitlab_events(
        request=mock_request,
        x_gitlab_token='test_token',
        x_openhands_webhook_id='test_webhook_id',
        x_openhands_user_id='test_user_id',
    )

    # Verify Redis was called to set the key with the hash
    mock_redis.set.assert_called_once_with(expected_key, 1, nx=True, ex=60)

    # Verify the message was NOT processed (duplicate)
    assert not mock_gitlab_manager.receive_message.called
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    # mypy: disable-error-code="unreachable"
    response_body = json.loads(response.body)  # type: ignore
    assert response_body['message'] == 'Duplicate GitLab event ignored.'