async def test_reauth(hass: HomeAssistant) -> None:
    """Test a reauth."""
    config_data = {
        CONF_URL: TEST_URL,
        CONF_WEBHOOK_ID: "test-webhook-id",
    }

    config_entry = create_mock_motioneye_config_entry(hass, data=config_data)

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    mock_client = create_mock_motioneye_client()

    new_data = {
        CONF_URL: TEST_URL,
        CONF_ADMIN_USERNAME: "admin-username",
        CONF_ADMIN_PASSWORD: "admin-password",
        CONF_SURVEILLANCE_USERNAME: "surveillance-username",
        CONF_SURVEILLANCE_PASSWORD: "surveillance-password",
    }

    with (
        patch(
            "homeassistant.components.motioneye.MotionEyeClient",
            return_value=mock_client,
        ),
        patch(
            "homeassistant.components.motioneye.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            new_data,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert dict(config_entry.data) == {**new_data, CONF_WEBHOOK_ID: "test-webhook-id"}

    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_client.async_client_close.called