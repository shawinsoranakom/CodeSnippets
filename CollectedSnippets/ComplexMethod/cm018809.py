async def test_validation_options(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test validation."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "options"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "missing_max_age_or_sampling_size"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_KEEP_LAST_SAMPLE: True, CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0},
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "options"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "missing_keep_last_sample"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["version"] == 1
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: "sensor.test_monitored",
        CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
        CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
        CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
        CONF_KEEP_LAST_SAMPLE: False,
        CONF_PERCENTILE: 50.0,
        CONF_PRECISION: 2.0,
    }

    assert len(mock_setup_entry.mock_calls) == 1