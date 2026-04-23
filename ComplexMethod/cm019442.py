async def test_unload_config_entry(hass: HomeAssistant) -> None:
    """Test unloading a config entry."""
    assert hass.state is CoreState.running

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )
    entry.add_to_hass(hass)

    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]

    timestamp = future_timestamp(100)
    with patch(
        "homeassistant.components.cert_expiry.coordinator.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        assert await async_setup_component(hass, DOMAIN, {}) is True
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")

    await hass.config_entries.async_unload(entry.entry_id)

    assert entry.state is ConfigEntryState.NOT_LOADED
    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state.state == STATE_UNAVAILABLE

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state is None