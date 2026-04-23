async def test_polling_cancellation_on_success(hass: HomeAssistant) -> None:
    """Test that polling is cancelled when device becomes claimed successfully during auth_and_claim."""
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
        # Subsequent client for polling check - device now claimed
        mock_client = MagicMock()

        async def auth_success():
            nonlocal auth_call_count
            auth_call_count += 1
            return True

        mock_client.authenticate = auth_success
        mock_client.recordNumber = TEST_RECORD_NUMBER
        mock_client.recordName = TEST_RECORD_NAME
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

        # Start auth_and_claim flow - sets up polling task
        result_external = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: TEST_PROVISIONING_KEY,
                CONF_PROVISIONING_SECRET: TEST_PROVISIONING_SECRET,
            },
        )
        assert result_external["type"] is FlowResultType.EXTERNAL_STEP

        # Wait for polling to detect the device is claimed and advance the flow
        await hass.async_block_till_done()

        # Verify polling made authentication attempt
        assert auth_call_count == 2  # One for polling, one for the final check

        # User continues - device is already claimed, polling should be cancelled
        result_done = await hass.config_entries.flow.async_configure(
            result_external["flow_id"]
        )
        assert result_done["type"] is FlowResultType.CREATE_ENTRY

        # Verify polling was cancelled - the auth count should not increase
        assert auth_call_count == 2

        # Wait a bit and verify no further authentication attempts from polling
        await hass.async_block_till_done()
        final_auth_count = auth_call_count

        # Ensure all background tasks have completed and polling really stopped
        await hass.async_block_till_done()

        # No new auth attempts should have occurred (polling was cancelled)
        assert auth_call_count == final_auth_count