async def test_readings_login_error_triggers_reauth(
    hass: HomeAssistant,
    mock_freshr_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a LoginError during readings refresh triggers a reauth flow."""
    assert not hass.config_entries.flow.async_progress_by_handler(DOMAIN)

    mock_freshr_client.fetch_device_current.reset_mock()
    mock_freshr_client.fetch_device_current.side_effect = LoginError("session expired")
    freezer.tick(READINGS_SCAN_INTERVAL)
    async_fire_time_changed(hass, freezer())
    await hass.async_block_till_done()

    assert mock_freshr_client.fetch_device_current.called

    assert mock_config_entry.state is ConfigEntryState.LOADED

    entity_ids = [
        entry.entity_id
        for entry in er.async_entries_for_config_entry(
            entity_registry, mock_config_entry.entry_id
        )
    ]
    assert entity_ids
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state is not None, f"State for {entity_id} is None"
        assert state.state == STATE_UNAVAILABLE, (
            f"Expected {entity_id} to be {STATE_UNAVAILABLE!r}, got {state.state!r}"
        )

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    relevant_flows = [
        {
            "entry_id": flow.get("context", {}).get("entry_id"),
            "source": flow.get("context", {}).get("source"),
            "step_id": flow.get("step_id"),
        }
        for flow in flows
    ]
    assert any(
        flow["entry_id"] == mock_config_entry.entry_id
        and flow["source"] == SOURCE_REAUTH
        and flow["step_id"] == "reauth_confirm"
        for flow in relevant_flows
    ), (
        "Expected a reauth_confirm flow for the config entry, "
        f"but found flows: {relevant_flows}"
    )