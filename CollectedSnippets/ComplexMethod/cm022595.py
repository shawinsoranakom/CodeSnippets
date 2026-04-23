async def test_reauth_flow_errors_with_recovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_liebherr_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test reauth flow error handling with successful recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"

    # Trigger error
    mock_liebherr_client.get_devices.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new-api-key"}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": expected_error}

    # Recover and complete successfully
    mock_liebherr_client.get_devices.side_effect = None
    new_api_key = "new-api-key-recovered"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: new_api_key}
    )
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"
    assert mock_config_entry.data[CONF_API_KEY] == new_api_key