async def test_rpc_rgbw_device_light_mode_remove_others(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Shelly RPC RGBW device in light mode removes RGB/RGBW entities."""
    monkeypatch.delitem(mock_rpc_device.status, "rgb:0")
    monkeypatch.delitem(mock_rpc_device.status, "rgbw:0")

    # register rgb and rgbw lights
    config_entry = await init_integration(hass, 2, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    register_entity(
        hass,
        LIGHT_DOMAIN,
        "test_rgb_0",
        "rgb:0",
        config_entry,
        device_id=device_entry.id,
    )
    register_entity(
        hass,
        LIGHT_DOMAIN,
        "test_rgbw_0",
        "rgbw:0",
        config_entry,
        device_id=device_entry.id,
    )

    # verify RGB & RGBW entities created
    assert get_entity(hass, LIGHT_DOMAIN, "rgb:0") is not None
    assert get_entity(hass, LIGHT_DOMAIN, "rgbw:0") is not None

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # verify we have 4 lights
    for i in range(SHELLY_PLUS_RGBW_CHANNELS):
        entity_id = f"light.test_light_{i}"

        assert (state := hass.states.get(entity_id))
        assert state.state == STATE_ON

        assert (entry := entity_registry.async_get(entity_id))
        assert entry.unique_id == f"123456789ABC-light:{i}"

    # verify RGB & RGBW entities removed
    assert get_entity(hass, LIGHT_DOMAIN, "rgb:0") is None
    assert get_entity(hass, LIGHT_DOMAIN, "rgbw:0") is None