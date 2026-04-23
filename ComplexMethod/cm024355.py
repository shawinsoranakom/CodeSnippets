async def test_unit_conversion_priority_precision(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    unit_system,
    native_unit,
    automatic_unit,
    suggested_unit,
    custom_unit,
    suggested_precision,
    native_value,
    native_state,
    automatic_state,
    suggested_state,
    custom_state,
    device_class,
) -> None:
    """Test priority of unit conversion for sensors with suggested_display_precision."""

    hass.config.units = unit_system

    entity0 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_display_precision=suggested_precision,
        unique_id="very_unique",
    )
    entity1 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_display_precision=suggested_precision,
    )
    entity2 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_display_precision=suggested_precision,
        suggested_unit_of_measurement=suggested_unit,
        unique_id="very_unique_2",
    )
    entity3 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_display_precision=suggested_precision,
        suggested_unit_of_measurement=suggested_unit,
    )
    entity4 = MockSensor(
        name="Test",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_display_precision=None,
        unique_id="very_unique_4",
    )
    setup_test_component_platform(
        hass,
        sensor.DOMAIN,
        [
            entity0,
            entity1,
            entity2,
            entity3,
            entity4,
        ],
    )

    assert await async_setup_component(hass, "sensor", {"sensor": {"platform": "test"}})
    await hass.async_block_till_done()

    # Registered entity -> Follow automatic unit conversion
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(automatic_state)
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit
    # Assert the automatic unit conversion is stored in the registry
    entry = entity_registry.async_get(entity0.entity_id)
    assert entry.unit_of_measurement == automatic_unit
    assert entry.options == {
        "sensor": {"suggested_display_precision": 2},
        "sensor.private": {"suggested_unit_of_measurement": automatic_unit},
    }
    assert float(async_rounded_state(hass, entity0.entity_id, state)) == pytest.approx(
        round(automatic_state, 2)
    )

    # Unregistered entity -> Follow native unit
    state = hass.states.get(entity1.entity_id)
    assert state.state == native_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == native_unit

    # Registered entity with suggested unit
    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == pytest.approx(suggested_state)
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity2.entity_id)
    assert entry.unit_of_measurement == suggested_unit
    assert entry.options == {
        "sensor": {"suggested_display_precision": 2},
        "sensor.private": {"suggested_unit_of_measurement": suggested_unit},
    }

    # Unregistered entity with suggested unit
    state = hass.states.get(entity3.entity_id)
    assert float(state.state) == pytest.approx(suggested_state)
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit

    # Set a custom unit, this should have priority over the automatic unit conversion
    entity_registry.async_update_entity_options(
        entity0.entity_id, "sensor", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(custom_state)
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    entity_registry.async_update_entity_options(
        entity2.entity_id, "sensor", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == pytest.approx(custom_state)
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    # Set a display_precision, this should have priority over suggested_display_precision
    entity_registry.async_update_entity_options(
        entity0.entity_id,
        "sensor",
        {"suggested_display_precision": 2, "display_precision": 4},
    )
    entry0 = entity_registry.async_get(entity0.entity_id)
    assert entry0.options["sensor"]["suggested_display_precision"] == 2
    assert entry0.options["sensor"]["display_precision"] == 4
    await hass.async_block_till_done()
    assert float(async_rounded_state(hass, entity0.entity_id, state)) == pytest.approx(
        round(custom_state, 4)
    )

    # Set a display_precision without having suggested_display_precision
    entity_registry.async_update_entity_options(
        entity4.entity_id,
        "sensor",
        {"display_precision": 4},
    )
    entry4 = entity_registry.async_get(entity4.entity_id)
    assert entry4.options["sensor"]["display_precision"] == 4
    await hass.async_block_till_done()
    state = hass.states.get(entity4.entity_id)
    assert float(async_rounded_state(hass, entity4.entity_id, state)) == pytest.approx(
        round(automatic_state, 4)
    )