async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_waterfurnace_client: Mock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test successful reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "new_user", CONF_PASSWORD: "new_password"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.title == "WaterFurnace new_user"
    assert mock_config_entry.data[CONF_USERNAME] == "new_user"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_password"