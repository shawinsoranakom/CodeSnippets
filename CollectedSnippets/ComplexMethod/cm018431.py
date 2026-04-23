async def test_custom_unit_change(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    native_unit,
    custom_unit,
    used_custom_unit,
    default_unit,
    native_value,
    custom_value,
    default_value,
) -> None:
    """Test custom unit changes are picked up."""
    entity0 = common.MockNumberEntity(
        name="Test",
        native_value=native_value,
        native_unit_of_measurement=native_unit,
        device_class=NumberDeviceClass.TEMPERATURE,
        unique_id="very_unique",
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    # Default unit conversion according to unit system
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(default_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == default_unit

    entity_registry.async_update_entity_options(
        "number.test", "number", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    # Unit conversion to the custom unit
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(custom_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == used_custom_unit

    entity_registry.async_update_entity_options(
        "number.test", "number", {"unit_of_measurement": native_unit}
    )
    await hass.async_block_till_done()

    # Unit conversion to another custom unit
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(native_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == native_unit

    entity_registry.async_update_entity_options("number.test", "number", None)
    await hass.async_block_till_done()

    # Default unit conversion according to unit system
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(default_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == default_unit