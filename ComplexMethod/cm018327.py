async def test_update_intervals(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, tomorrowio_config_entry_update
) -> None:
    """Test coordinator update intervals."""
    data = _get_config_schema(hass, SOURCE_USER)(MIN_CONFIG)
    data[CONF_NAME] = "test"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options={CONF_TIMESTEP: 1},
        unique_id=_get_unique_id(hass, data),
        version=1,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert len(tomorrowio_config_entry_update.call_args_list) == 1

    tomorrowio_config_entry_update.reset_mock()

    # Before the update interval, no updates yet
    freezer.tick(timedelta(minutes=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(tomorrowio_config_entry_update.call_args_list) == 0

    tomorrowio_config_entry_update.reset_mock()

    # On the update interval, we get a new update
    freezer.tick(timedelta(minutes=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(tomorrowio_config_entry_update.call_args_list) == 1

    tomorrowio_config_entry_update.reset_mock()

    # Adding a second config entry should cause the update interval to double
    config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options={CONF_TIMESTEP: 1},
        unique_id=f"{_get_unique_id(hass, data)}_1",
        version=1,
    )
    config_entry_2.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_2.entry_id)
    await hass.async_block_till_done()
    assert config_entry.data[CONF_API_KEY] == config_entry_2.data[CONF_API_KEY]
    # We should get an immediate call once the new config entry is setup for a
    # partial update
    assert len(tomorrowio_config_entry_update.call_args_list) == 1

    tomorrowio_config_entry_update.reset_mock()

    # We should get no new calls on our old interval
    freezer.tick(timedelta(minutes=32))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(tomorrowio_config_entry_update.call_args_list) == 0

    tomorrowio_config_entry_update.reset_mock()

    # We should get two calls on our new interval, one for each entry
    freezer.tick(timedelta(minutes=32))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(tomorrowio_config_entry_update.call_args_list) == 2

    tomorrowio_config_entry_update.reset_mock()