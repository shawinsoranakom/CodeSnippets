async def test_reauth_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test login errors."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "homeassistant.components.totalconnect.config_flow.TotalConnectClient",
    ) as client:
        client.side_effect = AuthenticationError()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: PASSWORD}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"