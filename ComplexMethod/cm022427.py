async def test_setup_and_remove_config_entry(hass: HomeAssistant) -> None:
    """Test setting up and removing a config entry."""
    # Setup the config entry
    config_entry = MockConfigEntry(domain=sun.DOMAIN)
    config_entry.add_to_hass(hass)
    now = datetime(2016, 6, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(now):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Check the platform is setup correctly
    state = hass.states.get(entity.ENTITY_ID)
    assert state is not None

    test_time = dt_util.parse_datetime(
        hass.states.get(entity.ENTITY_ID).attributes[entity.STATE_ATTR_NEXT_RISING]
    )
    assert test_time is not None
    assert hass.states.get(entity.ENTITY_ID).state == sun.STATE_BELOW_HORIZON

    # Remove the config entry
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state is removed, and does not reappear
    assert hass.states.get(entity.ENTITY_ID) is None

    patched_time = test_time + timedelta(seconds=5)
    with freeze_time(patched_time):
        async_fire_time_changed(hass, patched_time)
        await hass.async_block_till_done()

    assert hass.states.get(entity.ENTITY_ID) is None