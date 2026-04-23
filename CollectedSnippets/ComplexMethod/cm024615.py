async def test_attributes_from_entry_config(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test attributes from entry config."""

    await init_integration(
        hass,
        title="Get Value - With",
        options={
            CONF_QUERY: "SELECT 5 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {
                CONF_UNIT_OF_MEASUREMENT: "MiB",
                CONF_DEVICE_CLASS: SensorDeviceClass.DATA_SIZE,
                CONF_STATE_CLASS: SensorStateClass.TOTAL,
            },
        },
        entry_id="8693d4782ced4fb1ecca4743f29ab8f1",
    )

    state = hass.states.get("sensor.get_value_with")
    assert state.state == "5"
    assert state.attributes["value"] == 5
    assert state.attributes[CONF_UNIT_OF_MEASUREMENT] == "MiB"
    assert state.attributes[CONF_DEVICE_CLASS] == SensorDeviceClass.DATA_SIZE
    assert state.attributes[CONF_STATE_CLASS] == SensorStateClass.TOTAL

    await init_integration(
        hass,
        title="Get Value - Without",
        options={
            CONF_QUERY: "SELECT 6 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {
                CONF_UNIT_OF_MEASUREMENT: "MiB",
            },
        },
        entry_id="7aec7cd8045fba4778bb0621469e3cd9",
    )

    state = hass.states.get("sensor.get_value_without")
    assert state.state == "6"
    assert state.attributes["value"] == 6
    assert state.attributes[CONF_UNIT_OF_MEASUREMENT] == "MiB"
    assert CONF_DEVICE_CLASS not in state.attributes
    assert CONF_STATE_CLASS not in state.attributes