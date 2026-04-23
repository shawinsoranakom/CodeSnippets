async def test_ssdp_no_friendly_name(hass: HomeAssistant, fritz: Mock) -> None:
    """Test starting a flow from discovery without friendly name."""
    MOCK_NO_NAME = dataclasses.replace(MOCK_SSDP_DATA["ip4_valid"])
    MOCK_NO_NAME.upnp = MOCK_NO_NAME.upnp.copy()
    del MOCK_NO_NAME.upnp[ATTR_UPNP_FRIENDLY_NAME]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_NO_NAME
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "fake_pass", CONF_USERNAME: "fake_user"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.0.0.1"
    assert result["data"][CONF_HOST] == "10.0.0.1"
    assert result["data"][CONF_PASSWORD] == "fake_pass"
    assert result["data"][CONF_USERNAME] == "fake_user"
    assert result["result"].unique_id == "only-a-test"