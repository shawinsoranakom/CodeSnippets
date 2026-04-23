async def test_zeroconf_auth_failure(
    hass: HomeAssistant, mock_charger: MagicMock
) -> None:
    """Test zeroconf discovery with connection failure."""
    mock_charger.test_and_get.side_effect = [
        AuthenticationError,
        AuthenticationError,
        {},
    ]
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.123"),
        ip_addresses=[ip_address("192.168.1.123"), ip_address("2001:db8::1")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "192.168.1.123",
        CONF_USERNAME: "fakeuser",
        CONF_PASSWORD: "muchpassword",
    }