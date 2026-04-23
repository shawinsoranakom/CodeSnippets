async def test_reauth_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_verisure_config_flow: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test a reauthentication flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result.get("step_id") == "reauth_confirm"
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "correct horse battery staple",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.ABORT
    assert result2.get("reason") == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_GIID: "12345",
        CONF_EMAIL: "verisure_my_pages@example.com",
        CONF_PASSWORD: "correct horse battery staple",
    }

    assert len(mock_verisure_config_flow.login.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1