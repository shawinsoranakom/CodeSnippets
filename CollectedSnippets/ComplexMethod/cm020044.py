async def test_reauth_flow(
    hass: HomeAssistant,
    mock_setup: Mock,
    config_entry: MockConfigEntry,
) -> None:
    """Test the controller is setup correctly."""
    assert config_entry.data.get(CONF_PASSWORD) == "old-password"
    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result.get("step_id") == "reauth_confirm"
    assert not result.get("errors")

    # Simluate the wrong password
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "incorrect_password"},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"
    assert result.get("errors") == {"base": "invalid_auth"}

    # Enter the correct password and complete the flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: PASSWORD},
    )
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.unique_id == MAC_ADDRESS_UNIQUE_ID
    assert entry.data.get(CONF_PASSWORD) == PASSWORD

    assert len(mock_setup.mock_calls) == 1