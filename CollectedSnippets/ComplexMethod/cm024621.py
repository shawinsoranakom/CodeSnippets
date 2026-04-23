async def test_device_state_class(hass: HomeAssistant) -> None:
    """Test we get the form."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_DATA_CONFIG,
        options={
            CONF_QUERY: "SELECT 5 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {
                CONF_UNIT_OF_MEASUREMENT: "MiB",
            },
        },
        version=2,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_QUERY: "SELECT 5 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {
                CONF_UNIT_OF_MEASUREMENT: "MiB",
                CONF_DEVICE_CLASS: SensorDeviceClass.DATA_SIZE,
                CONF_STATE_CLASS: SensorStateClass.TOTAL,
            },
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
        CONF_ADVANCED_OPTIONS: {
            CONF_UNIT_OF_MEASUREMENT: "MiB",
            CONF_DEVICE_CLASS: SensorDeviceClass.DATA_SIZE,
            CONF_STATE_CLASS: SensorStateClass.TOTAL,
        },
    }

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_QUERY: "SELECT 5 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {
                CONF_UNIT_OF_MEASUREMENT: "MiB",
            },
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_DEVICE_CLASS not in result["data"]
    assert CONF_STATE_CLASS not in result["data"]
    assert result["data"] == {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
        CONF_ADVANCED_OPTIONS: {
            CONF_UNIT_OF_MEASUREMENT: "MiB",
        },
    }