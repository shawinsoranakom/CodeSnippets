async def test_reauth_flow_handles_user_not_pressing_button(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry_v2: MockConfigEntry,
    mock_homewizardenergy_v2: MagicMock,
) -> None:
    """Test reauth flow token is updated."""

    mock_config_entry_v2.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry_v2.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry_v2.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm_update_token"
    assert result["errors"] is None

    # Simulate button not being pressed
    mock_homewizardenergy_v2.get_token.side_effect = DisabledError

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "authorization_failed"}

    # Simulate user pressing the button and getting a new token
    mock_homewizardenergy_v2.get_token.side_effect = None
    mock_homewizardenergy_v2.get_token.return_value = "cool_new_token"

    # Successful reauth
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    # Verify that the token was updated
    await hass.async_block_till_done()
    assert (
        hass.config_entries.async_entries(DOMAIN)[0].data.get(CONF_TOKEN)
        == "cool_new_token"
    )
    assert len(mock_setup_entry.mock_calls) == 2