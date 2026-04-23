async def test_flow_fails_invalid_column_name(hass: HomeAssistant) -> None:
    """Test config flow fails invalid column name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=DATA_CONFIG,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_COLUMN_NAME,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_COLUMN_NAME: "column_invalid",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Get Value"
    assert result["data"] == {}
    assert result["options"] == {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
        CONF_ADVANCED_OPTIONS: {
            CONF_UNIT_OF_MEASUREMENT: "MiB",
            CONF_DEVICE_CLASS: SensorDeviceClass.DATA_SIZE,
            CONF_STATE_CLASS: SensorStateClass.TOTAL,
        },
    }