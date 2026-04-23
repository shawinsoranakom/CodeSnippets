async def test_config_flow_invalid_interface(hass: HomeAssistant) -> None:
    """Failed flow manually initialized by the user with invalid interface."""
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
        "homeassistant.components.motion_blinds.gateway.AsyncMotionMulticast.Start_listen",
        side_effect=socket.gaierror,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: TEST_API_KEY},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_GATEWAY_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_API_KEY: TEST_API_KEY,
        const.CONF_INTERFACE: TEST_HOST_ANY,
    }