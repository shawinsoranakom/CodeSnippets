async def test_reauth_flow_failed_qr_code(
    hass: HomeAssistant,
    mock_tuya_login_control: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test an error occurring while retrieving the QR code."""
    mock_config_entry.add_to_hass(hass)

    # Something went wrong getting the QR code (like an invalid user code)
    mock_tuya_login_control.qr_code.return_value["success"] = False

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_user_code"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("errors") == {"base": "login_error"}

    # This time it worked out
    mock_tuya_login_control.qr_code.return_value["success"] = True

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )
    assert result3.get("step_id") == "scan"

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result3.get("type") is FlowResultType.ABORT
    assert result3.get("reason") == "reauth_successful"