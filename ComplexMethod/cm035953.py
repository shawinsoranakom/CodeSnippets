async def test_install_webhook_success(
        self, mock_gitlab_service, mock_webhook_store, sample_webhook
    ):
        """Test successful webhook installation."""
        # Arrange
        resource_type = GitLabResourceType.PROJECT
        resource_id = 'project-123'

        # Act
        webhook_id, status = await install_webhook_on_resource(
            gitlab_service=mock_gitlab_service,
            resource_type=resource_type,
            resource_id=resource_id,
            webhook_store=mock_webhook_store,
            webhook=sample_webhook,
        )

        # Assert
        assert webhook_id == 'webhook-id-123'
        assert status is None
        mock_gitlab_service.install_webhook.assert_called_once()
        mock_webhook_store.update_webhook.assert_called_once()
        # Verify update_webhook was called with correct fields (using keyword arguments)
        call_args = mock_webhook_store.update_webhook.call_args
        assert call_args[1]['webhook'] == sample_webhook
        update_fields = call_args[1]['update_fields']
        assert update_fields['webhook_exists'] is True
        assert update_fields['webhook_url'] == GITLAB_WEBHOOK_URL
        assert 'webhook_secret' in update_fields
        assert 'webhook_uuid' in update_fields
        assert 'scopes' in update_fields