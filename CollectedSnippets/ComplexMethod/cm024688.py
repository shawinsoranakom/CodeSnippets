async def test_humidifier_read_humidity(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit humidifier accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_humidifier_service)

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.ACTIVE: True,
            CharacteristicsTypes.RELATIVE_HUMIDITY_HUMIDIFIER_THRESHOLD: 75,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 45,
        },
    )
    assert state.state == "on"
    assert state.attributes["humidity"] == 75
    assert state.attributes["current_humidity"] == 45

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.ACTIVE: False,
            CharacteristicsTypes.RELATIVE_HUMIDITY_HUMIDIFIER_THRESHOLD: 10,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 30,
        },
    )
    assert state.state == "off"
    assert state.attributes["humidity"] == 10
    assert state.attributes["current_humidity"] == 30

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 3,
        },
    )
    assert state.attributes["humidity"] == 10
    assert state.attributes["current_humidity"] == 30
    assert state.state == "off"