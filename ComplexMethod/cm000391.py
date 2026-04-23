async def test_handle_insufficient_funds_sends_discord_alert_first_time(
    server: SpinTestServer,
):
    """Test that the first insufficient funds notification sends a Discord alert."""

    user_id = "test-user-123"
    graph_id = "test-graph-456"
    error = InsufficientBalanceError(
        message="Insufficient balance",
        user_id=user_id,
        balance=72,  # $0.72
        amount=-714,  # Attempting to spend $7.14
    )

    with patch(
        "backend.executor.billing.queue_notification"
    ) as mock_queue_notif, patch(
        "backend.executor.billing.get_notification_manager_client"
    ) as mock_get_client, patch(
        "backend.executor.billing.settings"
    ) as mock_settings, patch(
        "backend.executor.billing.redis"
    ) as mock_redis_module:

        # Setup mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_settings.config.frontend_base_url = "https://test.com"

        # Mock Redis to simulate first-time notification (set returns True)
        mock_redis_client = MagicMock()
        mock_redis_module.get_redis.return_value = mock_redis_client
        mock_redis_client.set.return_value = True  # Key was newly set

        # Create mock database client
        mock_db_client = MagicMock()
        mock_graph_metadata = MagicMock()
        mock_graph_metadata.name = "Test Agent"
        mock_db_client.get_graph_metadata.return_value = mock_graph_metadata
        mock_db_client.get_user_email_by_id.return_value = "test@example.com"

        # Test the insufficient funds handler
        billing.handle_insufficient_funds_notif(
            db_client=mock_db_client,
            user_id=user_id,
            graph_id=graph_id,
            e=error,
        )

        # Verify notification was queued
        mock_queue_notif.assert_called_once()
        notification_call = mock_queue_notif.call_args[0][0]
        assert notification_call.type == NotificationType.ZERO_BALANCE
        assert notification_call.user_id == user_id
        assert isinstance(notification_call.data, ZeroBalanceData)
        assert notification_call.data.current_balance == 72

        # Verify Redis was checked with correct key pattern
        expected_key = f"{INSUFFICIENT_FUNDS_NOTIFIED_PREFIX}:{user_id}:{graph_id}"
        mock_redis_client.set.assert_called_once()
        call_args = mock_redis_client.set.call_args
        assert call_args[0][0] == expected_key
        assert call_args[1]["nx"] is True

        # Verify Discord alert was sent
        mock_client.discord_system_alert.assert_called_once()
        discord_message = mock_client.discord_system_alert.call_args[0][0]
        assert "Insufficient Funds Alert" in discord_message
        assert "test@example.com" in discord_message
        assert "Test Agent" in discord_message