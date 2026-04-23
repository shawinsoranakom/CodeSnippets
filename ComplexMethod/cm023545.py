async def test_user_cloud_login(hass: HomeAssistant) -> None:
    """Test the cloud login flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "cloud_login"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_login"

    # Test successful cloud login
    with (
        patch(
            "homeassistant.components.switchbot.config_flow.fetch_cloud_devices",
            return_value=None,
        ),
        patch(
            "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
            return_value=[WOHAND_SERVICE_INFO],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpass",
            },
        )

    # Should proceed to device selection with single device, so go to confirm
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    # Confirm device setup
    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bot EEFF"
    assert result["data"] == {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_SENSOR_TYPE: "bot",
    }