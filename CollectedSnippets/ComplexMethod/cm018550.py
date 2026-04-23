async def test_block_set_value_auth_error(
    hass: HomeAssistant, mock_block_device: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test block device set value authentication error."""
    monkeypatch.setitem(
        mock_block_device.settings,
        "sleep_mode",
        {"period": 60, "unit": "m"},
    )
    monkeypatch.setattr(
        mock_block_device,
        "set_thermostat_state",
        AsyncMock(side_effect=InvalidAuthError),
    )
    entry = await init_integration(hass, 1, sleep_period=3600)

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert entry.state is ConfigEntryState.LOADED

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.test_name_valve_position", ATTR_VALUE: 30},
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