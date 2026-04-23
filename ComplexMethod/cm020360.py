async def test_communication_error(
    hass: HomeAssistant, mock_luftdaten: MagicMock
) -> None:
    """Test that no sensor is added while unable to communicate with API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    mock_luftdaten.get_data.side_effect = LuftdatenConnectionError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_SENSOR_ID: 12345},
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {CONF_SENSOR_ID: "cannot_connect"}

    mock_luftdaten.get_data.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_SENSOR_ID: 12345},
    )

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "12345"
    assert result3.get("data") == {
        CONF_SENSOR_ID: 12345,
        CONF_SHOW_ON_MAP: False,
    }