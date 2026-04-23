async def test_setup_network(transport_mock, hass: HomeAssistant) -> None:
    """Test we can setup network."""
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

    with patch("homeassistant.components.rfxtrx.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "10.10.0.1", "port": 1234}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RFXTRX"
    assert result["data"] == {
        "host": "10.10.0.1",
        "port": 1234,
        "device": None,
        "automatic_add": False,
        "devices": {},
    }