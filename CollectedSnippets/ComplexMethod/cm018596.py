async def test_block_rest_update_auth_error(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block REST update authentication error."""
    register_entity(hass, BINARY_SENSOR_DOMAIN, "test_name_cloud", "cloud")
    monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
    monkeypatch.setitem(mock_block_device.status, "uptime", 1)
    entry = await init_integration(hass, 1)

    monkeypatch.setattr(
        mock_block_device,
        "update_shelly",
        AsyncMock(side_effect=InvalidAuthError),
    )

    assert entry.state is ConfigEntryState.LOADED

    await mock_rest_update(hass, freezer)

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id