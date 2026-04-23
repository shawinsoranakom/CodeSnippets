async def test_unit_conversion_priority_suggested_unit_change(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    unit_system,
    native_unit,
    original_unit,
    suggested_unit,
    native_value,
    original_value,
    device_class,
) -> None:
    """Test priority of unit conversion."""

    hass.config.units = unit_system

    # Pre-register entities
    entry = entity_registry.async_get_or_create(
        "sensor", "test", "very_unique", unit_of_measurement=original_unit
    )
    entity_registry.async_update_entity_options(
        entry.entity_id,
        "sensor.private",
        {"suggested_unit_of_measurement": original_unit},
    )
    entry = entity_registry.async_get_or_create(
        "sensor", "test", "very_unique_2", unit_of_measurement=original_unit
    )
    entity_registry.async_update_entity_options(
        entry.entity_id,
        "sensor.private",
        {"suggested_unit_of_measurement": original_unit},
    )

    entity0 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        unique_id="very_unique",
    )
    entity1 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_unit_of_measurement=suggested_unit,
        unique_id="very_unique_2",
    )
    setup_test_component_platform(hass, sensor.DOMAIN, [entity0, entity1])

    assert await async_setup_component(hass, "sensor", {"sensor": {"platform": "test"}})
    await hass.async_block_till_done()

    # Registered entity -> Follow automatic unit conversion the first time the entity was seen
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(original_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == original_unit
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity0.entity_id)
    assert entry.unit_of_measurement == original_unit
    assert (
        entry.options["sensor.private"]["suggested_unit_of_measurement"]
        == original_unit
    )

    # Registered entity -> Follow suggested unit the first time the entity was seen
    state = hass.states.get(entity1.entity_id)
    assert float(state.state) == pytest.approx(float(original_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == original_unit
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity1.entity_id)
    assert entry.unit_of_measurement == original_unit
    assert (
        entry.options["sensor.private"]["suggested_unit_of_measurement"]
        == original_unit
    )