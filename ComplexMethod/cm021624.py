async def test_manual_errors(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
    side_effect: Exception,
    reason: str,
) -> None:
    """Test adding existing device updates existing entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "manual_entry"}
    )

    mock_lametric.device.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_API_KEY: "mock-api-key"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_entry"
    assert result["errors"] == {"base": reason}

    assert len(mock_lametric.device.mock_calls) == 1
    assert len(mock_lametric.notify.mock_calls) == 0

    mock_lametric.device.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_API_KEY: "mock-api-key"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "Frenck's LaMetric"
    assert config_entry.unique_id == "SA110405124500W00BS9"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_API_KEY: "mock-api-key",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }
    assert not config_entry.options

    assert len(mock_lametric.device.mock_calls) == 2
    assert len(mock_lametric.notify.mock_calls) == 1