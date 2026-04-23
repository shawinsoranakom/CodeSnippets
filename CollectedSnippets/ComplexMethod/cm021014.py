async def test_multiple_sections(
    hass: HomeAssistant,
) -> None:
    """Test that multiple sections are handled correctly."""
    hass.set_state(CoreState.not_running)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456789",
        data={
            CONF_ORIGIN_LATITUDE: float(ORIGIN_LATITUDE),
            CONF_ORIGIN_LONGITUDE: float(ORIGIN_LONGITUDE),
            CONF_DESTINATION_LATITUDE: float(DESTINATION_LATITUDE),
            CONF_DESTINATION_LONGITUDE: float(DESTINATION_LONGITUDE),
            CONF_API_KEY: API_KEY,
            CONF_MODE: TRAVEL_MODE_BICYCLE,
            CONF_NAME: "test",
        },
        options=DEFAULT_OPTIONS,
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    duration = hass.states.get("sensor.test_duration")
    assert duration.state == "18.4833333333333"

    assert float(hass.states.get("sensor.test_distance").state) == pytest.approx(3.583)
    assert (
        hass.states.get("sensor.test_duration_in_traffic").state == "18.4833333333333"
    )
    assert hass.states.get("sensor.test_origin").state == "Chemin de Halage"
    assert (
        hass.states.get("sensor.test_origin").attributes.get(ATTR_LATITUDE)
        == "49.1260894"
    )
    assert (
        hass.states.get("sensor.test_origin").attributes.get(ATTR_LONGITUDE)
        == "6.1843356"
    )

    assert hass.states.get("sensor.test_destination").state == "Rue Charles Sadoul"
    assert (
        hass.states.get("sensor.test_destination").attributes.get(ATTR_LATITUDE)
        == "49.1025668"
    )
    assert (
        hass.states.get("sensor.test_destination").attributes.get(ATTR_LONGITUDE)
        == "6.1768518"
    )