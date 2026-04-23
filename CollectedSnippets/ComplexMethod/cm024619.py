async def test_options_flow_fails_invalid_query(hass: HomeAssistant) -> None:
    """Test options flow fails incorrect query and template."""
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

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_QUERY_OPT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_invalid",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_QUERY_2_OPT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_INVALID_QUERY_3_OPT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_QUERY_NO_READ_ONLY_OPT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_QUERY_NO_READ_ONLY_CTE_OPT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "query_no_read_only",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=ENTRY_CONFIG_MULTIPLE_QUERIES_OPT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_QUERY: "multiple_queries",
    }

    message = re.escape("Schema validation failed @ data['query']")
    with pytest.raises(InvalidData, match=message):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG_WITH_BROKEN_QUERY_TEMPLATE_OPT,
        )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_QUERY: "SELECT 5 as size",
            CONF_COLUMN_NAME: "size",
            CONF_ADVANCED_OPTIONS: {
                CONF_UNIT_OF_MEASUREMENT: "MiB",
            },
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_QUERY: "SELECT 5 as size",
        CONF_COLUMN_NAME: "size",
        CONF_ADVANCED_OPTIONS: {
            CONF_UNIT_OF_MEASUREMENT: "MiB",
        },
    }