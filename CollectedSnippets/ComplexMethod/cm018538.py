async def test_rpc_rgbw_device_rgb_w_modes_remove_others(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
    active_mode: str,
    removed_mode: str,
) -> None:
    """Test Shelly RPC RGBW device in RGB/W modes other lights."""
    removed_key = f"{removed_mode}:0"
    config_entry = await init_integration(hass, 2, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)

    # register lights
    for i in range(SHELLY_PLUS_RGBW_CHANNELS):
        monkeypatch.delitem(mock_rpc_device.status, f"light:{i}")
        entity_id = f"light.test_name_test_light_{i}"
        register_entity(
            hass,
            LIGHT_DOMAIN,
            entity_id,
            f"light:{i}",
            config_entry,
            device_id=device_entry.id,
        )
    monkeypatch.delitem(mock_rpc_device.status, f"{removed_mode}:0")
    register_entity(
        hass,
        LIGHT_DOMAIN,
        f"test_{removed_key}",
        removed_key,
        config_entry,
        device_id=device_entry.id,
    )

    # verify lights entities created
    for i in range(SHELLY_PLUS_RGBW_CHANNELS):
        assert get_entity(hass, LIGHT_DOMAIN, f"light:{i}") is not None
    assert get_entity(hass, LIGHT_DOMAIN, removed_key) is not None

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # verify we have RGB/w light
    entity_id = f"light.test_name_test_{active_mode}_0"

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{active_mode}:0"

    # verify light & RGB/W entities removed
    for i in range(SHELLY_PLUS_RGBW_CHANNELS):
        assert get_entity(hass, LIGHT_DOMAIN, f"light:{i}") is None
    assert get_entity(hass, LIGHT_DOMAIN, removed_key) is None