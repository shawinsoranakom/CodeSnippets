async def test_stats_addon_sensor(
    hass: HomeAssistant,
    entity_id,
    expected,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
    addon_stats: AsyncMock,
) -> None:
    """Test stats addons sensor."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    assert await async_setup_component(
        hass,
        "hassio",
        {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
    )
    await hass.async_block_till_done()

    # Verify that the entity is disabled by default.
    assert hass.states.get(entity_id) is None

    addon_stats.side_effect = SupervisorError
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "Could not fetch stats" not in caplog.text

    addon_stats.side_effect = None
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "Could not fetch stats" not in caplog.text

    # Enable the entity and wait for the reload to complete.
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    freezer.tick(config_entries.RELOAD_AFTER_UPDATE_DELAY)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert config_entry.state is ConfigEntryState.LOADED
    # Verify the entity is still enabled
    assert entity_registry.async_get(entity_id).disabled_by is None

    # The config entry just reloaded, so we need to wait for the next update
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id) is not None

    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    # Verify that the entity have the expected state.
    state = hass.states.get(entity_id)
    assert state.state == expected

    addon_stats.side_effect = SupervisorError
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_UNAVAILABLE
    assert "Could not fetch stats" in caplog.text

    # Disable the entity again and verify stats API calls stop
    addon_stats.side_effect = None
    addon_stats.reset_mock()
    entity_registry.async_update_entity(
        entity_id, disabled_by=er.RegistryEntryDisabler.USER
    )
    freezer.tick(config_entries.RELOAD_AFTER_UPDATE_DELAY)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert config_entry.state is ConfigEntryState.LOADED

    # After reload with entity disabled, stats should not be fetched
    addon_stats.reset_mock()
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    addon_stats.assert_not_called()