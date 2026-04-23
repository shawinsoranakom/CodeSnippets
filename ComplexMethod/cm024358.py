async def test_unit_conversion_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    unit_system_1,
    unit_system_2,
    native_unit,
    automatic_unit_1,
    automatic_unit_2,
    suggested_unit,
    custom_unit,
    native_value,
    automatic_state_1,
    automatic_state_2,
    suggested_state,
    custom_state,
    device_class,
) -> None:
    """Test suggested unit can be updated."""

    hass.config.units = unit_system_1

    entity0 = MockSensor(
        name="Test 0",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        unique_id="very_unique",
    )

    entity1 = MockSensor(
        name="Test 1",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        unique_id="very_unique_1",
    )

    entity2 = MockSensor(
        name="Test 2",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_unit_of_measurement=suggested_unit,
        unique_id="very_unique_2",
    )

    entity3 = MockSensor(
        name="Test 3",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        suggested_unit_of_measurement=suggested_unit,
        unique_id="very_unique_3",
    )

    entity4 = MockSensor(
        name="Test 4",
        device_class=device_class,
        native_unit_of_measurement=native_unit,
        native_value=str(native_value),
        unique_id="very_unique_4",
    )

    entity_platform = MockEntityPlatform(
        hass, domain="sensor", platform_name="test", platform=None
    )
    await entity_platform.async_add_entities((entity0, entity1, entity2, entity3))

    # Pre-register entity4
    entry = entity_registry.async_get_or_create(
        "sensor", "test", entity4.unique_id, unit_of_measurement=automatic_unit_1
    )
    entity4_entity_id = entry.entity_id
    entity_registry.async_update_entity_options(
        entity4_entity_id,
        "sensor.private",
        {
            "suggested_unit_of_measurement": automatic_unit_1,
        },
    )

    await hass.async_block_till_done()

    # Registered entity -> Follow automatic unit conversion
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == automatic_state_1
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit_1
    # Assert the automatic unit conversion is stored in the registry
    entry = entity_registry.async_get(entity0.entity_id)
    assert entry.options["sensor.private"] == {
        "suggested_unit_of_measurement": automatic_unit_1
    }

    state = hass.states.get(entity1.entity_id)
    assert float(state.state) == automatic_state_1
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit_1
    # Assert the automatic unit conversion is stored in the registry
    entry = entity_registry.async_get(entity1.entity_id)
    assert entry.options["sensor.private"] == {
        "suggested_unit_of_measurement": automatic_unit_1
    }

    # Registered entity with suggested unit
    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == suggested_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity2.entity_id)
    assert entry.options["sensor.private"] == {
        "suggested_unit_of_measurement": suggested_unit
    }

    state = hass.states.get(entity3.entity_id)
    assert float(state.state) == suggested_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit
    # Assert the suggested unit is stored in the registry
    entry = entity_registry.async_get(entity3.entity_id)
    assert entry.options["sensor.private"] == {
        "suggested_unit_of_measurement": suggested_unit
    }

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

    # Change unit system, states and units should be unchanged
    hass.config.units = unit_system_2
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    state = hass.states.get(entity1.entity_id)
    assert float(state.state) == automatic_state_1
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit_1

    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    state = hass.states.get(entity3.entity_id)
    assert float(state.state) == suggested_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit

    # Update suggested unit
    async_update_suggested_units(hass)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    state = hass.states.get(entity1.entity_id)
    assert float(state.state) == automatic_state_2
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit_2

    state = hass.states.get(entity2.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == custom_unit

    state = hass.states.get(entity3.entity_id)
    assert float(state.state) == suggested_state
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == suggested_unit

    # Entity 4 still has a pending request to refresh entity options
    entry = entity_registry.async_get(entity4_entity_id)
    assert entry.options["sensor.private"] == {
        "refresh_initial_entity_options": True,
        "suggested_unit_of_measurement": automatic_unit_1,
    }

    # Add entity 4, the pending request to refresh entity options should be handled
    await entity_platform.async_add_entities((entity4,))

    state = hass.states.get(entity4_entity_id)
    assert float(state.state) == automatic_state_2
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == automatic_unit_2

    entry = entity_registry.async_get(entity4_entity_id)
    assert "sensor.private" not in entry.options