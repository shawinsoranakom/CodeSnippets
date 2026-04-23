async def test_polling_cancellation_on_auth_failure(hass: HomeAssistant) -> None:
    """Test that polling is cancelled when authentication fails during auth_and_claim."""
    call_count = 0
    auth_call_count = 0

    def mock_webhook_client(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First client for initial claimless auth
            mock_client = MagicMock()
            mock_client.authenticate = AsyncMock(return_value=False)
            mock_client.get_claim_info.return_value = {"claim_url": "http://claim.me"}
            return mock_client
        # Subsequent client for polling check - fails authentication
        mock_client = MagicMock()

        async def auth_with_error():
            nonlocal auth_call_count
            auth_call_count += 1
            raise ClientError("Connection failed")

        mock_client.authenticate = auth_with_error
        return mock_client

    with (
        patch(
            "homeassistant.components.energyid.config_flow.WebhookClient",
            side_effect=mock_webhook_client,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        # Check initial form
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        # Start auth_and_claim flow - sets up polling
        result_external = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: TEST_PROVISIONING_KEY,
                CONF_PROVISIONING_SECRET: TEST_PROVISIONING_SECRET,
            },
        )
        assert result_external["type"] is FlowResultType.EXTERNAL_STEP

        # Wait for polling task to encounter the error and stop
        await hass.async_block_till_done()

        # Verify polling stopped after the error
        # auth_call_count should be 1 (one failed attempt during polling)
        initial_auth_count = auth_call_count
        assert initial_auth_count == 1

        # Trigger user continuing the flow - polling should already be stopped
        result_failed = await hass.config_entries.flow.async_configure(
            result_external["flow_id"]
        )
        assert result_failed["type"] is FlowResultType.EXTERNAL_STEP
        assert result_failed["step_id"] == "auth_and_claim"

        # Wait a bit and verify no further authentication attempts occurred
        await hass.async_block_till_done()
        assert (
            auth_call_count == initial_auth_count + 1
        )