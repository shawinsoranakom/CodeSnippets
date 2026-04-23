async def test_unload_remove(hass: HomeAssistant, fritz: Mock) -> None:
    """Test unload and remove of integration."""
    fritz().get_devices.return_value = [FritzDeviceSwitchMock()]
    entity_id = f"{SWITCH_DOMAIN}.{CONF_FAKE_NAME}"

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG[DOMAIN][CONF_DEVICES][0],
        unique_id=entity_id,
    )
    entry.add_to_hass(hass)

    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get(entity_id)
    assert state

    await hass.config_entries.async_unload(entry.entry_id)

    assert fritz().logout.call_count == 1
    assert entry.state is ConfigEntryState.NOT_LOADED
    state = hass.states.get(entity_id)
    assert state.state == STATE_UNAVAILABLE

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert fritz().logout.call_count == 1
    assert entry.state is ConfigEntryState.NOT_LOADED
    state = hass.states.get(entity_id)
    assert state is None