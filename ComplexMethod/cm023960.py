async def test_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    mock_sonarr: MagicMock,
) -> None:
    """Test entity availability."""
    now = dt_util.utcnow()

    mock_config_entry.add_to_hass(hass)
    freezer.move_to(now)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(UPCOMING_ENTITY_ID)
    assert hass.states.get(UPCOMING_ENTITY_ID).state == "1"

    # state to unavailable
    mock_sonarr.async_get_calendar.side_effect = ArrException

    future = now + timedelta(minutes=1)
    freezer.move_to(future)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    assert hass.states.get(UPCOMING_ENTITY_ID)
    assert hass.states.get(UPCOMING_ENTITY_ID).state == STATE_UNAVAILABLE

    # state to available
    mock_sonarr.async_get_calendar.side_effect = None

    future += timedelta(minutes=1)
    freezer.move_to(future)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    assert hass.states.get(UPCOMING_ENTITY_ID)
    assert hass.states.get(UPCOMING_ENTITY_ID).state == "1"

    # state to unavailable
    mock_sonarr.async_get_calendar.side_effect = ArrException

    future += timedelta(minutes=1)
    freezer.move_to(future)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    assert hass.states.get(UPCOMING_ENTITY_ID)
    assert hass.states.get(UPCOMING_ENTITY_ID).state == STATE_UNAVAILABLE

    # state to available
    mock_sonarr.async_get_calendar.side_effect = None

    future += timedelta(minutes=1)
    freezer.move_to(future)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    assert hass.states.get(UPCOMING_ENTITY_ID)
    assert hass.states.get(UPCOMING_ENTITY_ID).state == "1"