async def test_setup_network_fail(transport_mock, hass: HomeAssistant) -> None:
    """Test we can setup network."""
    transport_mock.return_value.connect.side_effect = RFXtrxTransportError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Network"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_network"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "10.10.0.1", "port": 1234}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_network"
    assert result["errors"] == {"base": "cannot_connect"}