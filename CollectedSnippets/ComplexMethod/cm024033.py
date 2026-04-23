async def test_auth_timeout(
    hass: HomeAssistant,
    mock_tado_api: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the auth timeout."""
    mock_tado_api.device_activation_status.return_value = DeviceActivationStatus.PENDING

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.SHOW_PROGRESS_DONE
    assert result["step_id"] == "timeout"

    mock_tado_api.device_activation_status.return_value = (
        DeviceActivationStatus.COMPLETED
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "timeout"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "home name"
    assert result["data"] == {CONF_REFRESH_TOKEN: "refresh"}
    assert len(mock_setup_entry.mock_calls) == 1