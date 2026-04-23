async def test_invalid_sensor(hass: HomeAssistant, mock_luftdaten: MagicMock) -> None:
    """Test that an invalid sensor throws an error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    mock_luftdaten.validate_sensor.return_value = False
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_SENSOR_ID: 11111},
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {CONF_SENSOR_ID: "invalid_sensor"}

    mock_luftdaten.validate_sensor.return_value = True
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