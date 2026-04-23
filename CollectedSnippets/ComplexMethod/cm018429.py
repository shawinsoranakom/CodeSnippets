async def test_temperature_conversion(
    hass: HomeAssistant,
    unit_system,
    native_unit,
    state_unit,
    initial_native_value,
    initial_state_value,
    updated_native_value,
    updated_state_value,
    native_max_value,
    state_max_value,
    native_min_value,
    state_min_value,
    native_step,
    state_step,
) -> None:
    """Test temperature conversion."""
    hass.config.units = unit_system
    entity0 = common.MockNumberEntity(
        name="Test",
        native_max_value=native_max_value,
        native_min_value=native_min_value,
        native_step=native_step,
        native_unit_of_measurement=native_unit,
        native_value=initial_native_value,
        device_class=NumberDeviceClass.TEMPERATURE,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(initial_state_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == state_unit
    assert state.attributes[ATTR_MAX] == state_max_value
    assert state.attributes[ATTR_MIN] == state_min_value
    assert state.attributes[ATTR_STEP] == state_step

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: updated_state_value, ATTR_ENTITY_ID: entity0.entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(updated_state_value))
    assert entity0._values["native_value"] == updated_native_value

    # Set to the minimum value
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: state_min_value, ATTR_ENTITY_ID: entity0.entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(state_min_value), rel=0.1)

    # Set to the maximum value
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: state_max_value, ATTR_ENTITY_ID: entity0.entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(state_max_value), rel=0.1)