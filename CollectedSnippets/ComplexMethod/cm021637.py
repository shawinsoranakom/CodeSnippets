async def test_additional_device(hass: HomeAssistant) -> None:
    """Test that Flow can configure another device."""
    # Mock existing entry.
    entry = MockConfigEntry(domain=ps4.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)

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
        "pyps4_2ndscreen.Helper.has_devices",
        return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )

    with patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG_ADDITIONAL
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == MOCK_CREDS
    assert len(result["data"]["devices"]) == 1
    assert result["title"] == MOCK_TITLE