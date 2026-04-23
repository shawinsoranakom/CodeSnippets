async def test_form_sensor(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form for sensor."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_INDOOR_TEMP: "sensor.indoor_temp",
            CONF_INDOOR_HUMIDITY: "sensor.indoor_humidity",
            CONF_OUTDOOR_TEMP: "sensor.outdoor_temp",
            CONF_CALIBRATION_FACTOR: 2.0,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["version"] == 1
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_INDOOR_TEMP: "sensor.indoor_temp",
        CONF_INDOOR_HUMIDITY: "sensor.indoor_humidity",
        CONF_OUTDOOR_TEMP: "sensor.outdoor_temp",
        CONF_CALIBRATION_FACTOR: 2.0,
    }

    assert len(mock_setup_entry.mock_calls) == 1