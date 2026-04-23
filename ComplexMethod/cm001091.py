async def test_generic_api_error_keeps_notification_for_retry(
        self, notification_manager, sample_batch_event
    ):
        """Test that generic API errors keep notifications in batch for retry while others continue."""
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

            # Notification that failed with generic error
            failed_notifications = [notifications[1]]  # Only index 1 remains for retry

            # Setup mocks
            mock_db = mock_db_client.return_value
            mock_db.get_user_email_by_id = AsyncMock(return_value="test@example.com")
            mock_db.get_user_notification_batch = AsyncMock(
                side_effect=[
                    Mock(notifications=notifications),
                    Mock(
                        notifications=failed_notifications
                    ),  # Failed ones remain for retry
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

            # Track calls
            successful_indices = []
            failed_indices = []
            removed_notification_ids = []

            # Capture what gets removed
            def remove_side_effect(user_id, notif_type, notif_ids):
                removed_notification_ids.extend(notif_ids)
                return None

            mock_db.remove_notifications_from_batch.side_effect = remove_side_effect

            def send_side_effect(*args, **kwargs):
                data = kwargs.get("data", [])
                if isinstance(data, list) and len(data) == 1:
                    # Track which notification based on content
                    for i, notif in enumerate(notifications):
                        if any(
                            f"Test Agent {i}" in str(n.data)
                            for n in data
                            if hasattr(n, "data")
                        ):
                            # Index 1 has generic API error
                            if i == 1:
                                failed_indices.append(i)
                                raise Exception("Network timeout - temporary failure")
                            else:
                                successful_indices.append(i)
                                return None
                    return None
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
            assert len(successful_indices) == 4  # 4 succeeded (0, 2, 3, 4)
            assert len(failed_indices) == 1  # 1 failed
            assert 1 in failed_indices  # Index 1 failed

            # Verify generic error was logged
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any(
                "api error" in call.lower() or "skipping" in call.lower()
                for call in warning_calls
            )

            # Only successful ones should be removed from batch (failed one stays for retry)
            assert mock_db.remove_notifications_from_batch.call_count == 4
            assert (
                "notif_1" not in removed_notification_ids
            )  # Failed one NOT removed (stays for retry)
            assert "notif_0" in removed_notification_ids  # Successful one removed
            assert "notif_2" in removed_notification_ids  # Successful one removed
            assert "notif_3" in removed_notification_ids  # Successful one removed
            assert "notif_4" in removed_notification_ids