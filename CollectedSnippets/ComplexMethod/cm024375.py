async def test_zodiac_day(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    now: datetime,
    sign: str,
    element: str,
    modality: str,
) -> None:
    """Test the zodiac sensor."""
    await hass.config.async_set_time_zone("UTC")
    MockConfigEntry(
        domain=DOMAIN,
    ).add_to_hass(hass)

    with patch("homeassistant.components.zodiac.sensor.utcnow", return_value=now):
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zodiac")
    assert state
    assert state.state == sign
    assert state.attributes
    assert state.attributes[ATTR_ELEMENT] == element
    assert state.attributes[ATTR_MODALITY] == modality
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert state.attributes[ATTR_OPTIONS] == [
        "aquarius",
        "aries",
        "cancer",
        "capricorn",
        "gemini",
        "leo",
        "libra",
        "pisces",
        "sagittarius",
        "scorpio",
        "taurus",
        "virgo",
    ]

    entry = entity_registry.async_get("sensor.zodiac")
    assert entry
    assert entry.unique_id == "zodiac"
    assert entry.translation_key == "sign"