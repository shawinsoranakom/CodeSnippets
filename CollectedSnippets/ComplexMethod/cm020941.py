async def test_switch_auth_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nextdns_client: AsyncMock,
) -> None:
    """Tests that the turn on/off action starts re-auth flow."""
    await init_integration(hass, mock_config_entry)

    mock_nextdns_client.set_setting.side_effect = InvalidApiKeyError

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.fake_profile_block_page"},
        blocking=True,
    )

    assert mock_config_entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id