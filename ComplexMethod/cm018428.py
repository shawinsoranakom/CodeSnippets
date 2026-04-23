async def test_set_value(
    hass: HomeAssistant,
    mock_number_entities: list[MockNumberEntity],
) -> None:
    """Test we can only set valid values."""
    setup_test_component_platform(hass, DOMAIN, mock_number_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get("number.test")
    assert state.state == "50.0"
    assert state.attributes.get(ATTR_STEP) == 1.0

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: 60.0, ATTR_ENTITY_ID: "number.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("number.test")
    assert state.state == "60.0"

    # test range validation
    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_VALUE: 110.0, ATTR_ENTITY_ID: "number.test"},
            blocking=True,
        )
    assert exc.value.translation_domain == DOMAIN
    assert exc.value.translation_key == "out_of_range"
    assert (
        str(exc.value)
        == "Value 110.0 for number.test is outside valid range 0.0 - 100.0"
    )

    await hass.async_block_till_done()
    state = hass.states.get("number.test")
    assert state.state == "60.0"