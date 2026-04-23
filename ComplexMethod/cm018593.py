async def test_rpc_beta_update(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC device beta update entity."""
    entity_id = "update.test_name_beta_firmware"
    monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
    monkeypatch.setitem(
        mock_rpc_device.status["sys"],
        "available_updates",
        {
            "stable": {"version": "2"},
            "beta": {"version": ""},
        },
    )
    await init_integration(hass, 2)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1"
    assert state.attributes[ATTR_LATEST_VERSION] == "1"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    monkeypatch.setitem(
        mock_rpc_device.status["sys"],
        "available_updates",
        {
            "stable": {"version": "2"},
            "beta": {"version": "2b"},
        },
    )
    await mock_rest_update(hass, freezer)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1"
    assert state.attributes[ATTR_LATEST_VERSION] == "2b"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_RELEASE_URL] == GEN2_BETA_RELEASE_URL

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    inject_rpc_device_event(
        monkeypatch,
        mock_rpc_device,
        {
            "events": [
                {
                    "event": "ota_begin",
                    "id": 1,
                    "ts": 1668522399.2,
                }
            ],
            "ts": 1668522399.2,
        },
    )

    assert mock_rpc_device.trigger_ota_update.call_count == 1

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1"
    assert state.attributes[ATTR_LATEST_VERSION] == "2b"
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] == 0

    inject_rpc_device_event(
        monkeypatch,
        mock_rpc_device,
        {
            "events": [
                {
                    "event": "ota_progress",
                    "id": 1,
                    "ts": 1668522399.2,
                    "progress_percent": 40,
                }
            ],
            "ts": 1668522399.2,
        },
    )

    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] == 40

    inject_rpc_device_event(
        monkeypatch,
        mock_rpc_device,
        {
            "events": [
                {
                    "event": "ota_success",
                    "id": 1,
                    "ts": 1668522399.2,
                }
            ],
            "ts": 1668522399.2,
        },
    )
    monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2b")
    await mock_rest_update(hass, freezer)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "2b"
    assert state.attributes[ATTR_LATEST_VERSION] == "2b"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-sys-fwupdate_beta"