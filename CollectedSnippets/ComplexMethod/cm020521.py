async def test_reauth_errors(
    hass: HomeAssistant,
    mock_added_config_entry: MockConfigEntry,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
    error_type: Exception,
    errors_msg: str,
    error_placement: str,
) -> None:
    """Test reauth errors."""
    mock_added_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    assert mock_added_config_entry.state is ConfigEntryState.LOADED
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    [result] = flows
    assert result["step_id"] == "reauth_confirm"

    mock_device = mock_discovery["mock_devices"][IP_ADDRESS]
    with override_side_effect(mock_device.update, error_type):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )
    credentials = Credentials("fake_username", "fake_password")

    mock_discovery["discover_single"].assert_called_once_with(
        IP_ADDRESS, credentials=credentials, port=None
    )
    mock_device.update.assert_called_once_with()
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {error_placement: errors_msg}
    assert result2["description_placeholders"]["error"] == str(error_type)

    mock_discovery["discover_single"].reset_mock()
    mock_device.update.reset_mock(side_effect=True)
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )

    mock_discovery["discover_single"].assert_called_once_with(
        IP_ADDRESS, credentials=credentials, port=None
    )
    mock_device.update.assert_called_once_with()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"