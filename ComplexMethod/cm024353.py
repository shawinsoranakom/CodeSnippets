async def test_custom_unit_change(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    native_unit,
    custom_unit,
    state_unit,
    native_value,
    native_state,
    custom_state,
    device_class,
) -> None:
    """Test custom unit changes are picked up."""
    entity0 = MockSensor(
        name="Test",
        native_value=str(native_value),
        native_unit_of_measurement=native_unit,
        device_class=device_class,
        unique_id="very_unique",
    )
    setup_test_component_platform(hass, sensor.DOMAIN, [entity0])

    assert await async_setup_component(hass, "sensor", {"sensor": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == native_state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == native_unit

    entity_registry.async_update_entity_options(
        "sensor.test", "sensor", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == custom_state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == state_unit

    entity_registry.async_update_entity_options(
        "sensor.test", "sensor", {"unit_of_measurement": native_unit}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == native_state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == native_unit

    entity_registry.async_update_entity_options("sensor.test", "sensor", None)
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == native_state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == native_unit