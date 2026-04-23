async def test_update_auth_error_triggers_reauth(
    hass: HomeAssistant,
    mock_account: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test reauthentication flow is triggered on login error during update."""
    entry = await setup_integration(hass, mock_account, VACUUM_DOMAIN)

    assert (state := hass.states.get(VACUUM_ENTITY_ID))
    assert state.state != STATE_UNAVAILABLE

    # Simulate an authentication error during update
    mock_account.load_robots.side_effect = LitterRobotLoginException(
        "Invalid credentials"
    )
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get(VACUUM_ENTITY_ID))
    assert state.state == STATE_UNAVAILABLE

    # Ensure a reauthentication flow was triggered
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id