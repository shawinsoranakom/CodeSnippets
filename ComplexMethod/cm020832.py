async def test_reconfigure_exceptions(
    hass: HomeAssistant,
    mock_powerfox_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error: str,
) -> None:
    """Test exceptions during reconfiguration flow."""
    mock_powerfox_client.all_devices.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "new-email@powerfox.test",
            CONF_PASSWORD: "new-password",
        },
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": error}

    # Recover from error
    mock_powerfox_client.all_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "new-email@powerfox.test",
            CONF_PASSWORD: "new-password",
        },
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"

    assert len(hass.config_entries.async_entries()) == 1
    assert mock_config_entry.data[CONF_EMAIL] == "new-email@powerfox.test"
    assert mock_config_entry.data[CONF_PASSWORD] == "new-password"