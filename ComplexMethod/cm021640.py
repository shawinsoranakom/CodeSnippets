async def test_manual_mode_no_ip_error(hass: HomeAssistant) -> None:
    """Test no IP specified in manual mode throws an error."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "creds"

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mode"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"Config Mode": "Manual Entry"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mode"
    assert result["errors"] == {CONF_IP_ADDRESS: "no_ipaddress"}