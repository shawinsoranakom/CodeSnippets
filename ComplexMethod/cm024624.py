async def test_send_message_reauth_flow(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_aiontfy: AsyncMock,
    service: str,
    call_method,
) -> None:
    """Test unauthorized exception initiates reauth flow."""

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    getattr(mock_aiontfy, call_method).side_effect = (
        NtfyUnauthorizedAuthenticationError(40101, 401, "unauthorized"),
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_ENTITY_ID: "notify.mytopic", ATTR_SEQUENCE_ID: "Mc3otamDNcpJ"},
            blocking=True,
        )

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == config_entry.entry_id