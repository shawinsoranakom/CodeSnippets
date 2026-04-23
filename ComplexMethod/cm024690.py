async def test_humidifier_target_humidity_modes(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit humidifier accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_humidifier_service)

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.RELATIVE_HUMIDITY_HUMIDIFIER_THRESHOLD: 37,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 51,
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 1,
        },
    )
    assert state.attributes["mode"] == "auto"
    assert state.attributes["humidity"] == 37
    assert state.attributes["current_humidity"] == 51

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 3,
        },
    )
    assert state.attributes["mode"] == "normal"
    assert state.attributes["humidity"] == 37
    assert state.attributes["current_humidity"] == 51

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 2,
        },
    )
    assert state.attributes["mode"] == "normal"
    assert state.attributes["humidity"] == 37

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 0,
        },
    )
    assert state.attributes["mode"] == "normal"
    assert state.attributes["humidity"] == 37