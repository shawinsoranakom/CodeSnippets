async def test_setup_discovery(hass: HomeAssistant) -> None:
    """Test setting up Yeelight by discovery."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS, **CONFIG_ENTRY_DATA}
    )
    config_entry.add_to_hass(hass)

    mocked_bulb = _mocked_bulb()
    with _patch_discovery(), patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get(ENTITY_BINARY_SENSOR) is not None
    assert hass.states.get(ENTITY_LIGHT) is not None

    # Unload
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert hass.states.get(ENTITY_BINARY_SENSOR).state == STATE_UNAVAILABLE
    assert hass.states.get(ENTITY_LIGHT).state == STATE_UNAVAILABLE

    # Remove
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_BINARY_SENSOR) is None
    assert hass.states.get(ENTITY_LIGHT) is None