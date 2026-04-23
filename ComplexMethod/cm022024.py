async def test_user_flow_failed_scan(
    hass: HomeAssistant,
    mock_tuya_login_control: MagicMock,
) -> None:
    """Test an error occurring while verifying login."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "scan"

    # Access has been denied, or the code hasn't been scanned yet
    good_values = mock_tuya_login_control.login_result.return_value
    mock_tuya_login_control.login_result.return_value = (
        False,
        {"msg": "oops", "code": 42},
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result3.get("type") is FlowResultType.FORM
    assert result3.get("errors") == {"base": "login_error"}

    # This time it worked out
    mock_tuya_login_control.login_result.return_value = good_values

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result4.get("type") is FlowResultType.CREATE_ENTRY