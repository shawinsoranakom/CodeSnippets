async def test_miscale_v1_uuid(hass: HomeAssistant) -> None:
    """Test MiScale V1 UUID.

    This device uses a different UUID compared to the other Xiaomi sensors.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="50:FB:19:1B:B5:DC",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(hass, MISCALE_V1_SERVICE_INFO)

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    mass_non_stabilized_sensor = hass.states.get(
        "sensor.mi_smart_scale_b5dc_weight_non_stabilized"
    )
    mass_non_stabilized_sensor_attr = mass_non_stabilized_sensor.attributes
    assert mass_non_stabilized_sensor.state == "86.55"
    assert (
        mass_non_stabilized_sensor_attr[ATTR_FRIENDLY_NAME]
        == "Mi Smart Scale (B5DC) Weight non-stabilized"
    )
    assert mass_non_stabilized_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "kg"
    assert mass_non_stabilized_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    mass_sensor = hass.states.get("sensor.mi_smart_scale_b5dc_weight")
    mass_sensor_attr = mass_sensor.attributes
    assert mass_sensor.state == "86.55"
    assert mass_sensor_attr[ATTR_FRIENDLY_NAME] == "Mi Smart Scale (B5DC) Weight"
    assert mass_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "kg"
    assert mass_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()