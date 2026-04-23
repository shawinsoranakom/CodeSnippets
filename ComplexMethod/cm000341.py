async def test_basic_webhook_block(self):
        """Test creating a basic webhook block."""
        block = TestWebhookBlock()

        # Verify block configuration
        assert block.webhook_config is not None
        assert block.webhook_config.provider == "test_webhooks"
        assert block.webhook_config.webhook_type == "test"
        assert "{resource_id}" in block.webhook_config.resource_format  # type: ignore

        # Test block execution
        test_creds = APIKeyCredentials(
            id="test-webhook-creds",
            provider="test_webhooks",
            api_key=SecretStr("test-key"),
            title="Test Webhook Key",
        )

        outputs = {}
        async for name, value in block.run(
            TestWebhookBlock.Input(
                credentials={  # type: ignore
                    "provider": "test_webhooks",
                    "id": "test-webhook-creds",
                    "type": "api_key",
                },
                webhook_url="https://example.com/webhook",
                resource_id="resource_123",
                events=[TestWebhookTypes.CREATED, TestWebhookTypes.UPDATED],
            ),
            credentials=test_creds,
        ):
            outputs[name] = value

        assert outputs["webhook_id"] == "webhook_resource_123"
        assert outputs["is_active"] is True
        assert outputs["event_count"] == 2