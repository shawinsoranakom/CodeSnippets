async def test_rpc_sleeping_update(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC sleeping device update entity."""
    monkeypatch.setattr(mock_rpc_device, "connected", False)
    monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
    monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
    monkeypatch.setitem(
        mock_rpc_device.status["sys"],
        "available_updates",
        {
            "stable": {"version": "2"},
        },
    )
    entity_id = f"{UPDATE_DOMAIN}.test_name_firmware"
    await init_integration(hass, 2, sleep_period=1000)

    # Entity should be created when device is online
    assert hass.states.get(entity_id) is None

    # Make device online
    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1"
    assert state.attributes[ATTR_LATEST_VERSION] == "2"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == UpdateEntityFeature(0)
    assert state.attributes[ATTR_RELEASE_URL] == GEN2_RELEASE_URL

    monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "2"
    assert state.attributes[ATTR_LATEST_VERSION] == "2"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == UpdateEntityFeature(0)

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-sys-fwupdate"