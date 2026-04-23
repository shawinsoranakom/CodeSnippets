async def test_color_light(
    hass: HomeAssistant,
    device: MagicMock,
    extra_data: dict,
    expected_transition: float | None,
) -> None:
    """Test a color light and that all transitions are correctly passed."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    light = device.modules[Module.Light]

    # Setting color_temp to None emulates a device without color temp
    light.color_temp = None

    with _patch_discovery(device=device), _patch_connect(device=device):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "light.my_bulb"

    BASE_PAYLOAD = {ATTR_ENTITY_ID: entity_id}
    BASE_PAYLOAD |= extra_data

    state = hass.states.get(entity_id)
    assert state.state == "on"
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp", "hs"]

    assert attributes.get(ATTR_EFFECT) is None

    assert attributes[ATTR_COLOR_MODE] == "hs"
    assert attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 4000
    assert attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 9000
    assert attributes[ATTR_HS_COLOR] == (10, 30)
    assert attributes[ATTR_RGB_COLOR] == (255, 191, 178)
    assert attributes[ATTR_XY_COLOR] == (0.42, 0.336)

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, BASE_PAYLOAD, blocking=True
    )
    light.set_state.assert_called_once_with(
        LightState(light_on=False, transition=expected_transition)
    )
    light.set_state.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, BASE_PAYLOAD, blocking=True
    )
    light.set_state.assert_called_once_with(
        LightState(light_on=True, transition=expected_transition)
    )
    light.set_state.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {**BASE_PAYLOAD, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    light.set_brightness.assert_called_with(39, transition=expected_transition)
    light.set_brightness.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {**BASE_PAYLOAD, ATTR_COLOR_TEMP_KELVIN: 6666},
        blocking=True,
    )
    light.set_color_temp.assert_called_with(
        6666, brightness=None, transition=expected_transition
    )
    light.set_color_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {**BASE_PAYLOAD, ATTR_COLOR_TEMP_KELVIN: 6666},
        blocking=True,
    )
    light.set_color_temp.assert_called_with(
        6666, brightness=None, transition=expected_transition
    )
    light.set_color_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {**BASE_PAYLOAD, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    light.set_hsv.assert_called_with(10, 30, None, transition=expected_transition)
    light.set_hsv.reset_mock()