async def test_ecobee3_add_sensors_at_runtime(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test that new sensors are automatically added."""

    # Set up a base Ecobee 3 with no additional sensors.
    # There shouldn't be any entities but climate visible.
    accessories = await setup_accessories_from_file(hass, "ecobee3_no_sensors.json")
    await setup_test_accessories(hass, accessories)

    climate = entity_registry.async_get("climate.homew")
    assert climate.unique_id == "00:00:00:00:00:00_1_16"

    occ1 = entity_registry.async_get("binary_sensor.kitchen")
    assert occ1 is None

    occ2 = entity_registry.async_get("binary_sensor.porch")
    assert occ2 is None

    occ3 = entity_registry.async_get("binary_sensor.basement")
    assert occ3 is None

    # Now added 3 new sensors at runtime - sensors should appear and climate
    # shouldn't be duplicated.
    accessories = await setup_accessories_from_file(hass, "ecobee3.json")
    await device_config_changed(hass, accessories)

    occ1 = entity_registry.async_get("binary_sensor.kitchen")
    assert occ1.unique_id == "00:00:00:00:00:00_2_56"

    occ2 = entity_registry.async_get("binary_sensor.porch")
    assert occ2.unique_id == "00:00:00:00:00:00_3_56"

    occ3 = entity_registry.async_get("binary_sensor.basement")
    assert occ3.unique_id == "00:00:00:00:00:00_4_56"