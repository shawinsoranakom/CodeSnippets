async def test_remote_toggles(
    mock_hc, hass: HomeAssistant, mock_write_config, mock_config_entry: MockConfigEntry
) -> None:
    """Ensure calls to the remote also updates the switches."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # mocks start remote with Watch TV default activity
    state = hass.states.get(ENTITY_REMOTE)
    assert state.state == STATE_ON
    assert state.attributes.get("current_activity") == "Watch TV"

    # turn off remote
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_REMOTE},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_REMOTE)
    assert state.state == STATE_OFF
    assert state.attributes.get("current_activity") == "PowerOff"

    # turn on remote, restoring the last activity
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_REMOTE},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_REMOTE)
    assert state.state == STATE_ON
    assert state.attributes.get("current_activity") == "Watch TV"

    # send new activity command, with activity name
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_REMOTE, ATTR_ACTIVITY: "Play Music"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_REMOTE)
    assert state.state == STATE_ON
    assert state.attributes.get("current_activity") == "Play Music"

    # send new activity command, with activity id
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_REMOTE, ATTR_ACTIVITY: ACTIVITIES_TO_IDS["Watch TV"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_REMOTE)
    assert state.state == STATE_ON
    assert state.attributes.get("current_activity") == "Watch TV"