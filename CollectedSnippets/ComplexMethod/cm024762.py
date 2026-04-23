async def test_step_otp_exception(
    hass: HomeAssistant,
    mock_setup_entry,
    mock_request_otp,
    mock_submit_otp,
    mock__get_devices_metadata,
    expected_error,
) -> None:
    """Test user step with valid phone number."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PHONE: "+972555555555"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "otp"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"otp": "123456"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "otp"
    assert result["errors"] == {"base": expected_error}