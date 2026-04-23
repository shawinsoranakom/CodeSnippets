async def test_unit_conversion_priority_suggested_unit_change_2(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    native_unit_1,
    native_unit_2,
    suggested_unit,
    native_value,
    original_value,
    device_class,
) -> None:
    """Test priority of unit conversion."""

    hass.config.units = METRIC_SYSTEM

    # Pre-register entities
    entity_registry.async_get_or_create(
        "sensor", "test", "very_unique", unit_of_measurement=native_unit_1
    )
    entity_registry.async_get_or_create(
        "sensor", "test", "very_unique_2", unit_of_measurement=native_unit_1
    )

    entity0 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit_2,
        native_value=str(native_value),
        unique_id="very_unique",
    )
    entity1 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit_2,
        native_value=str(native_value),
        suggested_unit_of_measurement=suggested_unit,
        unique_id="very_unique_2",
    )
    setup_test_component_platform(hass, sensor.DOMAIN, [entity0, entity1])

    assert await async_setup_component(hass, "sensor", {"sensor": {"platform": "test"}})
    await hass.async_block_till_done()

    # Registered entity -> Follow unit in entity registry
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(original_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == native_unit_1
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity0.entity_id)
    assert entry.unit_of_measurement == native_unit_1
    assert (
        entry.options["sensor.private"]["suggested_unit_of_measurement"]
        == native_unit_1
    )

    # Registered entity -> Follow unit in entity registry
    state = hass.states.get(entity1.entity_id)
    assert float(state.state) == pytest.approx(float(original_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == native_unit_1
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity0.entity_id)
    assert entry.unit_of_measurement == native_unit_1
    assert (
        entry.options["sensor.private"]["suggested_unit_of_measurement"]
        == native_unit_1
    )