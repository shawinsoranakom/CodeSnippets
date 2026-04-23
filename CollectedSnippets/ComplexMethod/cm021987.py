async def test_form_with_options(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the flow with configuring options."""
    await hass.config.async_set_time_zone("America/Chicago")
    zone = await dt_util.async_get_time_zone("America/Chicago")
    # Oct 31st is a Friday. Unofficial holiday as Halloween
    freezer.move_to(datetime(2024, 10, 31, 12, 0, 0, tzinfo=zone))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_COUNTRY: "US",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "TX",
            CONF_CATEGORIES: [UNOFFICIAL],
        },
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "United States, TX"
    assert result["data"] == {
        CONF_COUNTRY: "US",
        CONF_PROVINCE: "TX",
    }
    assert result["options"] == {
        CONF_CATEGORIES: ["unofficial"],
    }

    state = hass.states.get("calendar.united_states_tx")
    assert state
    assert state.state == STATE_ON

    entries = hass.config_entries.async_entries(DOMAIN)
    entry = entries[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_CATEGORIES: []},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_CATEGORIES: [],
    }

    state = hass.states.get("calendar.united_states_tx")
    assert state
    assert state.state == STATE_OFF