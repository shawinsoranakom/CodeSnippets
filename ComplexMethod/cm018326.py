async def test_reauth_exception(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_client: MagicMock,
) -> None:
    """Test an unexpected exception during a reauth flow."""
    # Force a reauth
    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass,
        "auth-connect-address.json",
    )
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login-failure.json",
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}

    # Perform a reauth with an unknown exception
    mock_client.auth.connect_to_address.side_effect = Exception("UnknownException")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}

    assert len(mock_client.auth.connect_to_address.mock_calls) == 1

    # Complete the reauth without an exception
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login.json",
    )
    mock_client.auth.connect_to_address.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"