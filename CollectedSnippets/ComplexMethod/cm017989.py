async def test_setup_race_only_setup_once(hass: HomeAssistant) -> None:
    """Test ensure that config entries are only setup once."""
    attempts = 0
    slow_config_entry_setup_future = hass.loop.create_future()
    fast_config_entry_setup_future = hass.loop.create_future()
    slow_setup_future = hass.loop.create_future()

    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Mock setup."""
        await slow_setup_future
        return True

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock setup entry."""
        slow = entry.data["slow"]
        if slow:
            await slow_config_entry_setup_future
            return True
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConfigEntryNotReady
        await fast_config_entry_setup_future
        return True

    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock unload entry."""
        return True

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup=async_setup,
            async_setup_entry=async_setup_entry,
            async_unload_entry=async_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)

    entry = MockConfigEntry(domain="comp", data={"slow": False})
    entry.add_to_hass(hass)

    entry2 = MockConfigEntry(domain="comp", data={"slow": True})
    entry2.add_to_hass(hass)
    await entry2.setup_lock.acquire()

    async def _async_reload_entry(entry: MockConfigEntry):
        async with entry.setup_lock:
            await entry.async_unload(hass)
            await entry.async_setup(hass)

    hass.async_create_task(_async_reload_entry(entry2))

    setup_task = hass.async_create_task(async_setup_component(hass, "comp", {}))
    entry2.setup_lock.release()

    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert entry2.state is config_entries.ConfigEntryState.NOT_LOADED

    assert "comp" not in hass.config.components
    slow_setup_future.set_result(None)
    await asyncio.sleep(0)
    assert "comp" in hass.config.components

    assert entry.state is config_entries.ConfigEntryState.SETUP_RETRY
    assert entry2.state is config_entries.ConfigEntryState.SETUP_IN_PROGRESS

    fast_config_entry_setup_future.set_result(None)
    # Make sure setup retry is started
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=5))
    slow_config_entry_setup_future.set_result(None)
    await hass.async_block_till_done()

    assert entry.state is config_entries.ConfigEntryState.LOADED
    await hass.async_block_till_done()

    assert attempts == 2
    await hass.async_block_till_done()
    assert setup_task.done()
    assert entry2.state is config_entries.ConfigEntryState.LOADED