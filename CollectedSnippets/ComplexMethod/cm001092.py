async def test_batch_all_notifications_sent_successfully(
        self, notification_manager, sample_batch_event
    ):
        """Test successful batch processing where all notifications are sent without errors."""
        with patch("backend.notifications.notifications.logger") as mock_logger, patch(
            "backend.notifications.notifications.get_database_manager_async_client"
        ) as mock_db_client, patch(
            "backend.notifications.notifications.generate_unsubscribe_link"
        ) as mock_unsub_link:

            # Create batch of 5 notifications
            notifications = []
            for i in range(5):
                notification = Mock()
                notification.id = f"notif_{i}"
                notification.type = NotificationType.AGENT_RUN
                notification.data = {
                    "agent_name": f"Test Agent {i}",
                    "credits_used": 10.0 * (i + 1),
                    "execution_time": 5.0 * (i + 1),
                    "node_count": 3 + i,
                    "graph_id": f"graph_{i}",
                    "outputs": [],
                }
                notification.created_at = datetime.now(timezone.utc)
                notifications.append(notification)

            # Setup mocks
            mock_db = mock_db_client.return_value
            mock_db.get_user_email_by_id = AsyncMock(return_value="test@example.com")
            mock_db.get_user_notification_batch = AsyncMock(
                side_effect=[
                    Mock(notifications=notifications),
                    Mock(notifications=[]),  # Empty after all sent successfully
                ]
            )
            mock_db.remove_notifications_from_batch = AsyncMock()
            mock_unsub_link.return_value = "http://example.com/unsub"

            # Mock internal methods
            notification_manager._should_email_user_based_on_preference = AsyncMock(
                return_value=True
            )
            notification_manager._should_batch = AsyncMock(return_value=True)
            notification_manager._parse_message = Mock(return_value=sample_batch_event)

            # Track successful sends
            successful_indices = []
            removed_notification_ids = []

            # Capture what gets removed
            def remove_side_effect(user_id, notif_type, notif_ids):
                removed_notification_ids.extend(notif_ids)
                return None

            mock_db.remove_notifications_from_batch.side_effect = remove_side_effect

            def send_side_effect(*args, **kwargs):
                data = kwargs.get("data", [])
                if isinstance(data, list) and len(data) == 1:
                    # Track which notification was sent
                    for i, notif in enumerate(notifications):
                        if any(
                            f"Test Agent {i}" in str(n.data)
                            for n in data
                            if hasattr(n, "data")
                        ):
                            successful_indices.append(i)
                            return None
                    return None  # Success
                # Force single processing
                raise Exception("Force single processing")

            notification_manager.email_sender.send_templated.side_effect = (
                send_side_effect
            )

            # Act
            result = await notification_manager._process_batch(
                sample_batch_event.model_dump_json()
            )

            # Assert
            assert result is True

            # All 5 notifications should be sent successfully
            assert len(successful_indices) == 5
            assert successful_indices == [0, 1, 2, 3, 4]

            # All notifications should be removed from batch
            assert mock_db.remove_notifications_from_batch.call_count == 5
            assert len(removed_notification_ids) == 5
            for i in range(5):
                assert f"notif_{i}" in removed_notification_ids

            # No errors should be logged
            assert mock_logger.error.call_count == 0

            # Info message about successful sends should be logged
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("sent and removed" in call.lower() for call in info_calls)