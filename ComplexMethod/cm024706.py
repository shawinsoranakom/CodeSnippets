async def test_ecobee3_remove_sensors_at_runtime(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test that sensors are automatically removed."""

    # Set up a base Ecobee 3 with additional sensors.
    accessories = await setup_accessories_from_file(hass, "ecobee3.json")
    await setup_test_accessories(hass, accessories)

    climate = entity_registry.async_get("climate.homew")
    assert climate.unique_id == "00:00:00:00:00:00_1_16"

    occ1 = entity_registry.async_get("binary_sensor.kitchen")
    assert occ1.unique_id == "00:00:00:00:00:00_2_56"

    occ2 = entity_registry.async_get("binary_sensor.porch")
    assert occ2.unique_id == "00:00:00:00:00:00_3_56"

    occ3 = entity_registry.async_get("binary_sensor.basement")
    assert occ3.unique_id == "00:00:00:00:00:00_4_56"

    assert hass.states.get("binary_sensor.kitchen") is not None
    assert hass.states.get("binary_sensor.porch") is not None
    assert hass.states.get("binary_sensor.basement") is not None

    # Now remove 3 new sensors at runtime - sensors should disappear and climate
    # shouldn't be duplicated.
    accessories = await setup_accessories_from_file(hass, "ecobee3_no_sensors.json")
    await device_config_changed(hass, accessories)

    assert hass.states.get("binary_sensor.kitchen") is None
    assert entity_registry.async_get("binary_sensor.kitchen") is None

    assert hass.states.get("binary_sensor.porch") is None
    assert entity_registry.async_get("binary_sensor.porch") is None

    assert hass.states.get("binary_sensor.basement") is None
    assert entity_registry.async_get("binary_sensor.basement") is None

    # Now add the sensors back
    accessories = await setup_accessories_from_file(hass, "ecobee3.json")
    await device_config_changed(hass, accessories)

    occ1 = entity_registry.async_get("binary_sensor.kitchen")
    assert occ1.unique_id == "00:00:00:00:00:00_2_56"

    occ2 = entity_registry.async_get("binary_sensor.porch")
    assert occ2.unique_id == "00:00:00:00:00:00_3_56"

    occ3 = entity_registry.async_get("binary_sensor.basement")
    assert occ3.unique_id == "00:00:00:00:00:00_4_56"

    # Ensure the sensors are back
    assert hass.states.get("binary_sensor.kitchen") is not None
    assert occ1.id == entity_registry.async_get("binary_sensor.kitchen").id

    assert hass.states.get("binary_sensor.porch") is not None
    assert occ2.id == entity_registry.async_get("binary_sensor.porch").id

    assert hass.states.get("binary_sensor.basement") is not None
    assert occ3.id == entity_registry.async_get("binary_sensor.basement").id