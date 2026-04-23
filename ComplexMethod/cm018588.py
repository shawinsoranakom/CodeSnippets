async def test_block_version_compare(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device custom firmware version comparison."""

    STABLE = "20230913-111730/v1.14.0-gcb84623"
    BETA = "20231107-162609/v1.14.1-rc1-g0617c15"

    entity_id_beta = "update.test_name_beta_firmware"
    entity_id_latest = "update.test_name_firmware"
    monkeypatch.setitem(mock_block_device.status["update"], "old_version", STABLE)
    monkeypatch.setitem(mock_block_device.status["update"], "new_version", "")
    monkeypatch.setitem(mock_block_device.status["update"], "beta_version", BETA)
    monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
    await init_integration(hass, 1)

    assert (state := hass.states.get(entity_id_latest))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == STABLE
    assert state.attributes[ATTR_LATEST_VERSION] == STABLE

    assert (state := hass.states.get(entity_id_beta))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == STABLE
    assert state.attributes[ATTR_LATEST_VERSION] == BETA

    monkeypatch.setitem(mock_block_device.status["update"], "old_version", BETA)
    monkeypatch.setitem(mock_block_device.status["update"], "new_version", STABLE)
    monkeypatch.setitem(mock_block_device.status["update"], "beta_version", BETA)
    await mock_rest_update(hass, freezer)

    assert (state := hass.states.get(entity_id_latest))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == BETA
    assert state.attributes[ATTR_LATEST_VERSION] == STABLE

    assert (state := hass.states.get(entity_id_beta))
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == BETA
    assert state.attributes[ATTR_LATEST_VERSION] == BETA