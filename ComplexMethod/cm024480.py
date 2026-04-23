async def test_config_flow_discovery_2_success(hass: HomeAssistant) -> None:
    """Successful flow with 2 gateway discovered."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.motion_blinds.config_flow.MotionDiscovery.discover",
        return_value=TEST_DISCOVERY_2,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select"
    assert result["data_schema"].schema["select_ip"].container == [
        TEST_HOST,
        TEST_HOST2,
    ]
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"select_ip": TEST_HOST2},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "connect"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.motion_blinds.gateway.MotionGateway.Check_gateway_multicast",
        side_effect=socket.timeout,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: TEST_API_KEY},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_GATEWAY_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST2,
        CONF_API_KEY: TEST_API_KEY,
        const.CONF_INTERFACE: TEST_HOST_ANY,
    }