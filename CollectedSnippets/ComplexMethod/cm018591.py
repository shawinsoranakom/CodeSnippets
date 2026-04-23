async def test_rpc_restored_sleeping_update(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC restored update entity."""
    entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
    device = register_device(device_registry, entry)
    entity_id = register_entity(
        hass,
        UPDATE_DOMAIN,
        "test_name_firmware",
        "sys-fwupdate",
        entry,
        device_id=device.id,
    )

    attr = {ATTR_INSTALLED_VERSION: "1", ATTR_LATEST_VERSION: "2"}
    mock_restore_cache(hass, [State(entity_id, STATE_ON, attributes=attr)])
    monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2")
    monkeypatch.setitem(mock_rpc_device.status["sys"], "available_updates", {})
    monkeypatch.setattr(mock_rpc_device, "initialized", False)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1"
    assert state.attributes[ATTR_LATEST_VERSION] == "2"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == UpdateEntityFeature(0)

    # Make device online
    monkeypatch.setattr(mock_rpc_device, "initialized", True)
    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    # Mock update
    mock_rpc_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "2"
    assert state.attributes[ATTR_LATEST_VERSION] == "2"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == UpdateEntityFeature(0)