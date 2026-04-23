async def test_reauth(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test starting a flow by user to re-auth."""
    config_entry.add_to_hass(hass)
    # re-auth initialized
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with (
        patch(
            "homeassistant.components.tankerkoenig.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
        ) as mock_nearby_stations,
    ):
        # re-auth unsuccessful
        mock_nearby_stations.side_effect = TankerkoenigInvalidKeyError("Booom!")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "269534f6-aaaa-bbbb-cccc-yyyyzzzzxxxx",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}

        # re-auth successful
        mock_nearby_stations.side_effect = None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "269534f6-aaaa-bbbb-cccc-yyyyzzzzxxxx",
            },
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"

    mock_setup_entry.assert_called()

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    assert entry.data[CONF_API_KEY] == "269534f6-aaaa-bbbb-cccc-yyyyzzzzxxxx"