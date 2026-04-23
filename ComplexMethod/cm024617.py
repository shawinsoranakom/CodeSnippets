async def test_flow_fails_invalid_query(hass: HomeAssistant) -> None:
    """Test config flow fails incorrect db url."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == config_entries.SOURCE_USER

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=DATA_CONFIG,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_QUERY,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_invalid",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_QUERY_2,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_QUERY_3,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_QUERY_NO_READ_ONLY,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_QUERY_NO_READ_ONLY_CTE,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_MULTIPLE_QUERIES,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "multiple_queries",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_NO_RESULTS,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_invalid",
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