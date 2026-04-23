async def test_coordinator_error_handler_authentication_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_peblar: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the coordinator error handler with an authentication error."""

    # Ensure the sensor entity is now available.
    assert (state := hass.states.get("sensor.peblar_ev_charger_power"))
    assert state.state != STATE_UNAVAILABLE

    # Mock an authentication in the coordinator
    mock_peblar.rest_api.return_value.meter.side_effect = PeblarAuthenticationError(
        "Authentication error"
    )
    mock_peblar.login.side_effect = PeblarAuthenticationError("Authentication error")
    freezer.tick(timedelta(seconds=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Ensure the sensor entity is now unavailable.
    assert (state := hass.states.get("sensor.peblar_ev_charger_power"))
    assert state.state == STATE_UNAVAILABLE

    # Ensure we have triggered a reauthentication flow
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id