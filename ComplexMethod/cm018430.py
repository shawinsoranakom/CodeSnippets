async def test_restore_number_restore_state(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    native_max_value,
    native_min_value,
    native_step,
    native_value,
    native_value_type,
    extra_data,
    device_class,
    uom,
) -> None:
    """Test RestoreNumber."""
    mock_restore_cache_with_extra_data(hass, ((State("number.test", ""), extra_data),))

    entity0 = common.MockRestoreNumber(
        device_class=device_class,
        name="Test",
        native_value=None,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    assert hass.states.get(entity0.entity_id)

    assert entity0.native_max_value == native_max_value
    assert entity0.native_min_value == native_min_value
    assert entity0.native_step == native_step
    assert entity0.native_value == native_value
    assert type(entity0.native_value) is native_value_type
    assert entity0.native_unit_of_measurement == uom