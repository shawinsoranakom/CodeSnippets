async def test_unit_conversion_priority(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    unit_system,
    native_unit,
    automatic_unit,
    suggested_unit,
    custom_unit,
    native_value,
    native_state,
    automatic_state,
    suggested_state,
    custom_state,
    device_class,
) -> None:
    """Test priority of unit conversion."""

    hass.config.units = unit_system

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
    )
    entity2 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_unit_of_measurement=suggested_unit,
        unique_id="very_unique_2",
    )
    entity3 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_unit_of_measurement=suggested_unit,
    )
    setup_test_component_platform(
        hass,
        sensor.DOMAIN,
        [
            entity0,
            entity1,
            entity2,
            entity3,
        ],
    )

    assert await async_setup_component(hass, "sensor", {"sensor": {"platform": "test"}})
    await hass.async_block_till_done()

    # Registered entity -> Follow automatic unit conversion
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == automatic_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit
    # Assert the automatic unit conversion is stored in the registry
    entry = entity_registry.async_get(entity0.entity_id)
    assert entry.unit_of_measurement == automatic_unit
    assert (
        entry.options["sensor.private"]["suggested_unit_of_measurement"]
        == automatic_unit
    )

    # Unregistered entity -> Follow native unit
    state = hass.states.get(entity1.entity_id)
    assert float(state.state) == native_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == native_unit

    # Registered entity with suggested unit
    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == suggested_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity2.entity_id)
    assert entry.unit_of_measurement == suggested_unit
    assert (
        entry.options["sensor.private"]["suggested_unit_of_measurement"]
        == suggested_unit
    )

    # Unregistered entity with suggested unit
    state = hass.states.get(entity3.entity_id)
    assert float(state.state) == suggested_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit

    # Set a custom unit, this should have priority over the automatic unit conversion
    entity_registry.async_update_entity_options(
        entity0.entity_id, "sensor", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    entity_registry.async_update_entity_options(
        entity2.entity_id, "sensor", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit