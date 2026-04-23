async def test_block_beta_update(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device beta update entity."""
    entity_id = "update.test_name_beta_firmware"
    monkeypatch.setitem(mock_block_device.status["update"], "old_version", "1.0.0")
    monkeypatch.setitem(mock_block_device.status["update"], "new_version", "2.0.0")
    monkeypatch.setitem(mock_block_device.status["update"], "beta_version", "")
    monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
    await init_integration(hass, 1)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.0"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    monkeypatch.setitem(
        mock_block_device.status["update"], "beta_version", "2.0.0-beta"
    )
    await mock_rest_update(hass, freezer)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "2.0.0-beta"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert state.attributes[ATTR_RELEASE_URL] is None

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert mock_block_device.trigger_ota_update.call_count == 1

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "2.0.0-beta"
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    monkeypatch.setitem(mock_block_device.status["update"], "old_version", "2.0.0-beta")
    await mock_rest_update(hass, freezer)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "2.0.0-beta"
    assert state.attributes[ATTR_LATEST_VERSION] == "2.0.0-beta"
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-fwupdate_beta"