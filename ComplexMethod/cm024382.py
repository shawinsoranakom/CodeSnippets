async def test_reauth_reconnect(
    hass: HomeAssistant, client, freezer: FrozenDateTimeFactory
) -> None:
    """Test reauth flow triggered by reconnect."""
    entry = await setup_webostv(hass)
    client.is_connected.return_value = False
    client.connect.side_effect = WebOsTvPairError

    assert entry.state is ConfigEntryState.LOADED

    await mock_scan_interval(hass, freezer)

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id