async def test_manual_cannot_connect(
    hass: HomeAssistant,
    discovery_mock: MagicMock,
) -> None:
    """Test manual form transitions via cannot_connect to creation."""

    discovery_mock.discovers.side_effect = ControlPointError("Discovery failed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {}

    # First attempt fails with CANNOT_CONNECT when attempting to connect
    discovery_mock.return_value.validate_connection.side_effect = (
        ControlPointCannotConnectError
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: INPUT_HOST,
            CONF_PORT: INPUT_PORT,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "cannot_connect"}

    # Second attempt succeeds
    discovery_mock.return_value.validate_connection.side_effect = None
    discovery_mock.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: INPUT_HOST,
            CONF_PORT: INPUT_PORT,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"ZIMI Controller ({INPUT_HOST}:{INPUT_PORT})"
    assert result["data"] == {
        "host": INPUT_HOST,
        "port": INPUT_PORT,
        "mac": format_mac(INPUT_MAC),
    }