async def test_update_attrs_fails_on_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a smart plug auth failure."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)
    features = [
        _mocked_feature("brightness", value=50),
        _mocked_feature("hsv", value=(10, 30, 5)),
        _mocked_feature(
            "color_temp", value=4000, minimum_value=4000, maximum_value=9000
        ),
    ]
    light = _mocked_device(modules=[Module.Light], alias="my_light", features=features)
    light_module = light.modules[Module.Light]

    with _patch_discovery(device=light), _patch_connect(device=light):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "light.my_light"
    entity = entity_registry.async_get(entity_id)
    assert entity
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    p = PropertyMock(side_effect=KasaException)
    type(light_module).color_temp = p
    light.__str__ = lambda _: "MockLight"
    freezer.tick(5)
    async_fire_time_changed(hass)
    entity = entity_registry.async_get(entity_id)
    assert entity
    state = hass.states.get(entity_id)
    assert state.state == STATE_UNAVAILABLE
    assert f"Unable to read data for MockLight {entity_id}:" in caplog.text
    # Check only logs once
    caplog.clear()
    freezer.tick(5)
    async_fire_time_changed(hass)
    entity = entity_registry.async_get(entity_id)
    assert entity
    state = hass.states.get(entity_id)
    assert state.state == STATE_UNAVAILABLE
    assert f"Unable to read data for MockLight {entity_id}:" not in caplog.text