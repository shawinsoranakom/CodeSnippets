async def test_block_update_auth_error(
    hass: HomeAssistant,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device update authentication error."""
    monkeypatch.setitem(mock_block_device.status["update"], "old_version", "1.0.0")
    monkeypatch.setitem(mock_block_device.status["update"], "new_version", "2.0.0")
    monkeypatch.setattr(
        mock_block_device,
        "trigger_ota_update",
        AsyncMock(side_effect=InvalidAuthError),
    )
    entry = await init_integration(hass, 1)

    assert entry.state is ConfigEntryState.LOADED

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: "update.test_name_firmware"},
        blocking=True,
    )

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id