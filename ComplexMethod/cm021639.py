async def test_device_connection_error(hass: HomeAssistant) -> None:
    """Test that device not connected or on throws an error."""
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

    with patch(
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )

    with patch("pyps4_2ndscreen.Helper.link", return_value=(False, True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "cannot_connect"}