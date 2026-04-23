async def test_switch_read_light_state_hs(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit light accessory."""
    helper = await setup_test_component(
        hass, get_next_aid(), create_lightbulb_service_with_hs
    )

    # Initial state is that the light is off
    state = await helper.poll_and_get_state()
    assert state.state == "off"
    assert state.attributes[ATTR_COLOR_MODE] is None
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Simulate that someone switched on the device in the real world not via HA
    state = await helper.async_update(
        ServicesTypes.LIGHTBULB,
        {
            CharacteristicsTypes.ON: True,
            CharacteristicsTypes.BRIGHTNESS: 100,
            CharacteristicsTypes.HUE: 4,
            CharacteristicsTypes.SATURATION: 5,
        },
    )
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["hs_color"] == (4, 5)
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Simulate that device switched off in the real world not via HA
    state = await helper.async_update(
        ServicesTypes.LIGHTBULB,
        {
            CharacteristicsTypes.ON: False,
        },
    )
    assert state.state == "off"

    # Simulate that device switched on in the real world not via HA
    state = await helper.async_update(
        ServicesTypes.LIGHTBULB,
        {
            CharacteristicsTypes.ON: True,
            CharacteristicsTypes.HUE: 6,
            CharacteristicsTypes.SATURATION: 7,
        },
    )
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["hs_color"] == (6, 7)
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0