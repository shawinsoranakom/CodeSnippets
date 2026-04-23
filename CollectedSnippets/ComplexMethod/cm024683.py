async def test_switch_read_light_state_dimmer(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit light accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_lightbulb_service)

    # Initial state is that the light is off
    state = await helper.poll_and_get_state()
    assert state.state == "off"
    assert state.attributes[ATTR_COLOR_MODE] is None
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Simulate that someone switched on the device in the real world not via HA
    state = await helper.async_update(
        ServicesTypes.LIGHTBULB,
        {
            CharacteristicsTypes.ON: True,
            CharacteristicsTypes.BRIGHTNESS: 100,
        },
    )
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.BRIGHTNESS
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Simulate that device switched off in the real world not via HA
    state = await helper.async_update(
        ServicesTypes.LIGHTBULB,
        {
            CharacteristicsTypes.ON: False,
        },
    )
    assert state.state == "off"