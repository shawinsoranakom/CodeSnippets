async def test_422_permanently_removes_malformed_notification(
        self, notification_manager, sample_batch_event
    ):
        """Test that 422 error permanently removes the malformed notification from batch and continues with others."""
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
                    Mock(notifications=[]),  # Empty after processing
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
            call_count = [0]
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
                    current_call = call_count[0]
                    call_count[0] += 1

                    # Index 2 has malformed data (422)
                    if current_call == 2:
                        raise Exception(
                            "Unprocessable entity (422): Malformed email data"
                        )
                    else:
                        successful_indices.append(current_call)
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
            assert call_count[0] == 5  # All 5 attempted
            assert len(successful_indices) == 4  # 4 succeeded (all except index 2)
            assert 2 not in successful_indices  # Index 2 failed

            # Verify 422 error was logged
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any(
                "422" in call or "malformed" in call.lower() for call in warning_calls
            )

            # Verify all notifications were removed (4 successful + 1 malformed)
            assert mock_db.remove_notifications_from_batch.call_count == 5
            assert (
                "notif_2" in removed_notification_ids
            )