async def test_color_temp_light_no_color(hass: HomeAssistant) -> None:
    """Test a color temp light with no color."""
    device = _mocked_device(
        modules=[Module.Light],
        alias="my_light",
        features=[
            _mocked_feature("brightness", value=50),
            _mocked_feature(
                "color_temp", value=4000, minimum_value=4000, maximum_value=9000
            ),
        ],
    )
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)

    light = device.modules[Module.Light]

    with _patch_discovery(device=device), _patch_connect(device=device):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "light.my_light"

    state = hass.states.get(entity_id)
    assert state.state == "on"
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_COLOR_MODE] == "color_temp"

    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp"]
    assert attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 9000
    assert attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 4000
    assert attributes[ATTR_COLOR_TEMP_KELVIN] == 4000

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    light.set_state.assert_called_once()
    light.set_state.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    light.set_state.assert_called_once()
    light.set_state.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    light.set_brightness.assert_called_with(39, transition=None)
    light.set_brightness.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 6666},
        blocking=True,
    )
    light.set_color_temp.assert_called_with(6666, brightness=None, transition=None)
    light.set_color_temp.reset_mock()

    # Verify color temp is clamped to the valid range
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 20000},
        blocking=True,
    )
    light.set_color_temp.assert_called_with(9000, brightness=None, transition=None)
    light.set_color_temp.reset_mock()

    # Verify color temp is clamped to the valid range
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 1},
        blocking=True,
    )
    light.set_color_temp.assert_called_with(4000, brightness=None, transition=None)
    light.set_color_temp.reset_mock()