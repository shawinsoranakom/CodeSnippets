async def test_setup_connection_error(hass: HomeAssistant) -> None:
    """Test flow for setup with a connection error."""

    port = 1001
    host = "alarmdecoder"
    protocol = PROTOCOL_SOCKET
    connection_settings = {CONF_HOST: host, CONF_PORT: port}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "protocol"

    with (
        patch(
            "homeassistant.components.alarmdecoder.config_flow.AdExt.open",
            side_effect=NoDeviceError,
        ),
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.close"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], connection_settings
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "homeassistant.components.alarmdecoder.config_flow.AdExt.open",
            side_effect=Exception,
        ),
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.close"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], connection_settings
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}