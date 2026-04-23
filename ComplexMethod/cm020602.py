async def test_reconfigure_host_invalid(hass: HomeAssistant) -> None:
    """Test reconfigure flow retries on invalid host."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRYDATA_WEBSOCKET)
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch(
        "homeassistant.components.samsungtv.config_flow.socket.gethostbyname",
        side_effect=socket.gaierror("invalid host"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "bad-host"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == config_entries.SOURCE_RECONFIGURE
    assert result["errors"] == {"base": "invalid_host"}

    with patch(
        "homeassistant.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="10.10.12.77",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "new-host"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "10.10.12.77"