async def test_dehumidifier_read_humidity(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit dehumidifier accessory."""
    helper = await setup_test_component(
        hass, get_next_aid(), create_dehumidifier_service
    )

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.ACTIVE: True,
            CharacteristicsTypes.RELATIVE_HUMIDITY_DEHUMIDIFIER_THRESHOLD: 75,
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
            CharacteristicsTypes.RELATIVE_HUMIDITY_DEHUMIDIFIER_THRESHOLD: 40,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 39,
        },
    )
    assert state.state == "off"
    assert state.attributes["humidity"] == 40
    assert state.attributes["current_humidity"] == 39

    state = await helper.async_update(
        ServicesTypes.HUMIDIFIER_DEHUMIDIFIER,
        {
            CharacteristicsTypes.CURRENT_HUMIDIFIER_DEHUMIDIFIER_STATE: 2,
        },
    )
    assert state.attributes["humidity"] == 40