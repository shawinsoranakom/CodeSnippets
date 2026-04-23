async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_teltasync_client: MagicMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "new_password",
        },
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_USERNAME] == "admin"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_password"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.1"