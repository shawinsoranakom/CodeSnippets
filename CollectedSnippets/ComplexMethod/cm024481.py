async def test_config_flow_connection_error(hass: HomeAssistant) -> None:
    """Failed flow manually initialized by the user with connection timeout."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "connect"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.motion_blinds.gateway.MotionGateway.GetDeviceList",
        side_effect=socket.timeout,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: TEST_API_KEY},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "connection_error"