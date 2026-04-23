async def test_color_light_no_temp(hass: HomeAssistant) -> None:
    """Test a color light with no color temp."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    features = [
        _mocked_feature("brightness", value=50),
        _mocked_feature("hsv", value=(10, 30, 5)),
    ]

    device = _mocked_device(modules=[Module.Light], alias="my_light", features=features)
    light = device.modules[Module.Light]

    type(light).color_temp = PropertyMock(side_effect=Exception)
    with _patch_discovery(device=device), _patch_connect(device=device):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "light.my_light"

    state = hass.states.get(entity_id)
    assert state.state == "on"
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_COLOR_MODE] == "hs"
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
    assert attributes[ATTR_HS_COLOR] == (10, 30)
    assert attributes[ATTR_RGB_COLOR] == (255, 191, 178)
    assert attributes[ATTR_XY_COLOR] == (0.42, 0.336)

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
        {ATTR_ENTITY_ID: entity_id, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    light.set_hsv.assert_called_with(10, 30, None, transition=None)
    light.set_hsv.reset_mock()