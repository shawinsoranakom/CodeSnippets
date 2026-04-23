async def test_reauth(
    hass: HomeAssistant,
    mock_aiopurpleair,
    check_api_key_errors,
    check_api_key_mock,
    config_entry: MockConfigEntry,
    setup_config_entry,
) -> None:
    """Test re-auth (including errors)."""
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Test errors that can arise when checking the API key:
    with patch.object(mock_aiopurpleair, "async_check_api_key", check_api_key_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"api_key": "new_api_key"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == check_api_key_errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"api_key": "new_api_key"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert len(hass.config_entries.async_entries()) == 1
    # Unload to make sure the update does not run after the
    # mock is removed.
    await hass.config_entries.async_unload(config_entry.entry_id)