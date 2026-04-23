async def test_reauth_setup_entry(hass: HomeAssistant, client) -> None:
    """Test reauth flow triggered by setup entry."""
    client.is_connected.return_value = False
    client.connect.side_effect = WebOsTvPairError
    entry = await setup_webostv(hass)

    assert entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id