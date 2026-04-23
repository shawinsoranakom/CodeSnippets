async def test_validation_options(
    recorder_mock: Recorder, hass: HomeAssistant, mock_setup_entry: AsyncMock
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
            CONF_ENTITY_ID: "binary_sensor.test_monitored",
            CONF_TYPE: "count",
        },
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "state"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATE: ["on"],
        },
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "options"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
            CONF_END: "{{ utcnow() }}",
            CONF_DURATION: {"hours": 8, "minutes": 0, "seconds": 0, "days": 20},
        },
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "options"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "only_two_keys_allowed"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
            CONF_END: "{{ utcnow() }}",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["version"] == 1
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: "binary_sensor.test_monitored",
        CONF_STATE: ["on"],
        CONF_TYPE: "count",
        CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
        CONF_END: "{{ utcnow() }}",
    }

    assert len(mock_setup_entry.mock_calls) == 1