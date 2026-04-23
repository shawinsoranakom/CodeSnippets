async def test_ecobee3_services_and_chars_removed(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test handling removal of some services and chars."""

    # Set up a base Ecobee 3 with additional sensors.
    accessories = await setup_accessories_from_file(hass, "ecobee3.json")
    await setup_test_accessories(hass, accessories)

    climate = entity_registry.async_get("climate.homew")
    assert climate.unique_id == "00:00:00:00:00:00_1_16"

    assert hass.states.get("sensor.basement_temperature") is not None
    assert hass.states.get("sensor.kitchen_temperature") is not None
    assert hass.states.get("sensor.porch_temperature") is not None

    assert hass.states.get("select.homew_current_mode") is not None
    assert hass.states.get("button.homew_clear_hold") is not None

    # Reconfigure with some of the chars removed and the basement temperature sensor
    accessories = await setup_accessories_from_file(
        hass, "ecobee3_service_removed.json"
    )
    await device_config_changed(hass, accessories)

    # Make sure the climate entity is still there
    assert hass.states.get("climate.homew") is not None
    assert entity_registry.async_get("climate.homew") is not None

    # Make sure the basement temperature sensor is gone
    assert hass.states.get("sensor.basement_temperature") is None
    assert entity_registry.async_get("select.basement_temperature") is None

    # Make sure the current mode select and clear hold button are gone
    assert hass.states.get("select.homew_current_mode") is None
    assert entity_registry.async_get("select.homew_current_mode") is None

    assert hass.states.get("button.homew_clear_hold") is None
    assert entity_registry.async_get("button.homew_clear_hold") is None