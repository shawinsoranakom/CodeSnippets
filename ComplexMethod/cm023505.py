async def test_reauth_flow_retry(
    freezer: FrozenDateTimeFactory,
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test reauth works with retry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED

    mock_client.get_devices.side_effect = AOSmithInvalidCredentialsException(
        "Authentication error"
    )
    freezer.tick(REGULAR_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"

    # First attempt at reauth - authentication fails again
    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        side_effect=AOSmithInvalidCredentialsException("Authentication error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            {CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD]},
        )
        await hass.async_block_till_done()

        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] == {"base": "invalid_auth"}

    # Second attempt at reauth - authentication succeeds
    with (
        patch(
            "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
            return_value=[],
        ),
        patch("homeassistant.components.aosmith.async_setup_entry", return_value=True),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            {CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD]},
        )
        await hass.async_block_till_done()

        assert result3["type"] is FlowResultType.ABORT
        assert result3["reason"] == "reauth_successful"