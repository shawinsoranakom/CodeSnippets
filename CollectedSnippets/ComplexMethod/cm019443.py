async def test_delay_load_during_startup(hass: HomeAssistant) -> None:
    """Test delayed loading of a config entry during startup."""
    hass.set_state(CoreState.not_running)

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT})
    entry.add_to_hass(hass)

    assert await async_setup_component(hass, DOMAIN, {}) is True
    await hass.async_block_till_done()

    assert hass.state is CoreState.not_running
    assert entry.state is ConfigEntryState.LOADED

    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state is None

    timestamp = future_timestamp(100)
    with patch(
        "homeassistant.components.cert_expiry.coordinator.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        await hass.async_start()
        await hass.async_block_till_done()

    assert hass.state is CoreState.running

    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")