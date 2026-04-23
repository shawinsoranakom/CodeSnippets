async def test_gitlab_events_multiple_identical_payloads_deduplicated(
    mock_sio, mock_gitlab_manager, mock_verify_signature
):
    """Test that multiple identical GitLab events are properly deduplicated."""
    # Setup mocks
    mock_verify_signature.return_value = None
    mock_gitlab_manager.receive_message = AsyncMock()

    # Mock Redis
    mock_redis = AsyncMock()
    mock_sio.manager.redis = mock_redis

    # Create a payload with object_attributes.id
    payload = {
        'object_kind': 'merge_request',
        'object_attributes': {
            'id': 789,
            'title': 'Fix bug',
            'description': 'This fixes the bug',
            'state': 'opened',
        },
    }

    mock_request = MagicMock()
    mock_request.json = AsyncMock(return_value=payload)

    # First request - Redis returns True (key was set)
    mock_redis.set.return_value = True

    # Call the endpoint first time
    response1 = await gitlab_events(
        request=mock_request,
        x_gitlab_token='test_token',
        x_openhands_webhook_id='test_webhook_id',
        x_openhands_user_id='test_user_id',
    )

    # Verify Redis was called to set the key with the object_attributes.id
    mock_redis.set.assert_called_once_with(789, 1, nx=True, ex=60)
    mock_redis.set.reset_mock()

    # Verify the message was processed
    assert mock_gitlab_manager.receive_message.called
    assert isinstance(response1, JSONResponse)
    assert response1.status_code == 200
    assert (
        json.loads(response1.body)['message']
        == 'GitLab events endpoint reached successfully.'
    )
    mock_gitlab_manager.receive_message.reset_mock()

    # Second request - Redis returns False (key already exists)
    mock_redis.set.return_value = False

    # Call the endpoint second time with the same payload
    response2 = await gitlab_events(
        request=mock_request,
        x_gitlab_token='test_token',
        x_openhands_webhook_id='test_webhook_id',
        x_openhands_user_id='test_user_id',
    )

    # Verify Redis was called to set the key with the same object_attributes.id
    mock_redis.set.assert_called_once_with(789, 1, nx=True, ex=60)
    mock_redis.set.reset_mock()

    # Verify the message was NOT processed (duplicate)
    assert not mock_gitlab_manager.receive_message.called
    assert isinstance(response2, JSONResponse)
    assert response2.status_code == 200
    # mypy: disable-error-code="unreachable"
    response2_body = json.loads(response2.body)  # type: ignore
    assert response2_body['message'] == 'Duplicate GitLab event ignored.'

    # Third request - Redis returns False again (key still exists)
    mock_redis.set.return_value = False

    # Call the endpoint third time with the same payload
    response3 = await gitlab_events(
        request=mock_request,
        x_gitlab_token='test_token',
        x_openhands_webhook_id='test_webhook_id',
        x_openhands_user_id='test_user_id',
    )

    # Verify Redis was called to set the key with the same object_attributes.id
    mock_redis.set.assert_called_once_with(789, 1, nx=True, ex=60)

    # Verify the message was NOT processed (duplicate)
    assert not mock_gitlab_manager.receive_message.called
    assert isinstance(response3, JSONResponse)
    assert response3.status_code == 200
    # mypy: disable-error-code="unreachable"
    response3_body = json.loads(response3.body)  # type: ignore
    assert response3_body['message'] == 'Duplicate GitLab event ignored.'