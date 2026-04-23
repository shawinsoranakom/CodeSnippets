async def test_full_flow_not_recorder_db(
    hass: HomeAssistant,
    tmp_path: Path,
) -> None:
    """Test full config flow with not using recorder db."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    db_path = tmp_path / "db.db"
    db_path_str = f"sqlite:///{db_path}"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DB_URL: db_path_str,
            CONF_NAME: "Get Value",
        },
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_QUERY: "SELECT 5 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {},
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Get Value"
    assert result["data"] == {CONF_DB_URL: db_path_str}
    assert result["options"] == {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
        CONF_ADVANCED_OPTIONS: {},
    }

    entry = hass.config_entries.async_entries(DOMAIN)[0]

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
    assert result["data"] == {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
        CONF_ADVANCED_OPTIONS: {
            CONF_UNIT_OF_MEASUREMENT: "MiB",
        },
    }