async def test_discovered_dhcp(
    ismartgateapi_mock, async_setup_entry_mock, hass: HomeAssistant
) -> None:
    """Test we get the form with homekit and abort for dhcp source when we get both."""
    api: ISmartGateApi = MagicMock(spec=ISmartGateApi)
    ismartgateapi_mock.return_value = api

    api.reset_mock()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.2.3.4",
            macaddress=dr.format_mac(MOCK_MAC_ADDR).replace(":", ""),
            hostname="mock_hostname",
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result2
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
    api.reset_mock()

    closed_door_response = _mocked_ismartgate_closed_door_response()
    api.async_info.return_value = closed_door_response
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result3
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == {
        "device": "ismartgate",
        "ip_address": "1.2.3.4",
        "password": "password0",
        "username": "user0",
    }