async def test_miscale_v2_uuid(hass: HomeAssistant) -> None:
    """Test MiScale V2 UUID.

    This device uses a different UUID compared to the other Xiaomi sensors.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="50:FB:19:1B:B5:DC",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(hass, MISCALE_V2_SERVICE_INFO)

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3

    mass_non_stabilized_sensor = hass.states.get(
        "sensor.mi_body_composition_scale_b5dc_weight_non_stabilized"
    )
    mass_non_stabilized_sensor_attr = mass_non_stabilized_sensor.attributes
    assert mass_non_stabilized_sensor.state == "85.15"
    assert (
        mass_non_stabilized_sensor_attr[ATTR_FRIENDLY_NAME]
        == "Mi Body Composition Scale (B5DC) Weight non-stabilized"
    )
    assert mass_non_stabilized_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "kg"
    assert mass_non_stabilized_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    mass_sensor = hass.states.get("sensor.mi_body_composition_scale_b5dc_weight")
    mass_sensor_attr = mass_sensor.attributes
    assert mass_sensor.state == "85.15"
    assert (
        mass_sensor_attr[ATTR_FRIENDLY_NAME]
        == "Mi Body Composition Scale (B5DC) Weight"
    )
    assert mass_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "kg"
    assert mass_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    impedance_sensor = hass.states.get(
        "sensor.mi_body_composition_scale_b5dc_impedance"
    )
    impedance_sensor_attr = impedance_sensor.attributes
    assert impedance_sensor.state == "428"
    assert (
        impedance_sensor_attr[ATTR_FRIENDLY_NAME]
        == "Mi Body Composition Scale (B5DC) Impedance"
    )
    assert impedance_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "ohm"
    assert impedance_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()