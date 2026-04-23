async def test_scene_effect_light(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test activating a scene works with effects.

    i.e. doesn't try to set the effect to 'off'
    """
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    features = [
        _mocked_feature("brightness", value=50),
        _mocked_feature("hsv", value=(10, 30, 5)),
        _mocked_feature(
            "color_temp", value=4000, minimum_value=4000, maximum_value=9000
        ),
    ]
    device = _mocked_device(
        modules=[Module.Light, Module.LightEffect], alias="my_light", features=features
    )
    light_effect = device.modules[Module.LightEffect]
    light_effect.effect = LightEffect.LIGHT_EFFECTS_OFF

    with _patch_discovery(device=device), _patch_connect(device=device):
        assert await hass.config_entries.async_setup(
            already_migrated_config_entry.entry_id
        )
        assert await async_setup_component(hass, SCENE_DOMAIN, {})
        await hass.async_block_till_done()

    entity_id = "light.my_light"

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    freezer.tick(5)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state is STATE_ON
    assert state.attributes["effect"] is EFFECT_OFF

    await hass.services.async_call(
        SCENE_DOMAIN,
        SERVICE_CREATE,
        {CONF_SCENE_ID: "effect_off_scene", CONF_SNAPSHOT: [entity_id]},
        blocking=True,
    )
    await hass.async_block_till_done()
    scene_state = hass.states.get("scene.effect_off_scene")
    assert scene_state.state is STATE_UNKNOWN

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    freezer.tick(5)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state is STATE_OFF

    await hass.services.async_call(
        SCENE_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "scene.effect_off_scene",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    scene_state = hass.states.get("scene.effect_off_scene")
    assert scene_state.state is not STATE_UNKNOWN

    freezer.tick(5)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state is STATE_ON
    assert state.attributes["effect"] is EFFECT_OFF