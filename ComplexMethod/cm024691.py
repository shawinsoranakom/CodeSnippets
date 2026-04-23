async def test_dehumidifier_target_humidity_modes(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit dehumidifier accessory."""
    helper = await setup_test_component(
        hass, get_next_aid(), create_dehumidifier_service
    )

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.RELATIVE_HUMIDITY_DEHUMIDIFIER_THRESHOLD: 73,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 51,
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 1,
        },
    )
    assert state.attributes["mode"] == "auto"
    assert state.attributes["humidity"] == 73
    assert state.attributes["current_humidity"] == 51

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 3,
        },
    )
    assert state.attributes["mode"] == "normal"
    assert state.attributes["humidity"] == 73
    assert state.attributes["current_humidity"] == 51

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 2,
        },
    )
    assert state.attributes["mode"] == "normal"
    assert state.attributes["humidity"] == 73
    assert state.attributes["current_humidity"] == 51

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 0,
        },
    )
    assert state.attributes["mode"] == "normal"
    assert state.attributes["humidity"] == 73
    assert state.attributes["current_humidity"] == 51