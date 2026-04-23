async def test_user_cloud_login_unknown_error(hass: HomeAssistant) -> None:
    """Test the cloud login step shows unknown error for unexpected exceptions."""
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

    with patch(
        "homeassistant.components.switchbot.config_flow.fetch_cloud_devices",
        side_effect=Exception("Unexpected network failure"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpass",
            },
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_login"
    assert result["errors"] == {"base": "unknown"}

    # Recover: re-submit with valid credentials and successful cloud login
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

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

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