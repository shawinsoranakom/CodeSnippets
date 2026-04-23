async def test_ssdp(
    hass: HomeAssistant,
    login_requests_mock,
    requests_mock_request_kwargs,
    upnp_data,
    expected_result,
) -> None:
    """Test SSDP discovery initiates config properly."""
    url = FIXTURE_USER_INPUT[CONF_URL][:-1]  # strip trailing slash for appending port
    context = config_entries.ConfigFlowContext(source=config_entries.SOURCE_SSDP)
    login_requests_mock.request(**requests_mock_request_kwargs)
    service_info = SsdpServiceInfo(
        ssdp_usn="mock_usn",
        ssdp_st="upnp:rootdevice",
        ssdp_location=f"{url}:60957/rootDesc.xml",
        upnp={
            ATTR_UPNP_DEVICE_TYPE: "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
            ATTR_UPNP_MANUFACTURER: "Huawei",
            ATTR_UPNP_MANUFACTURER_URL: "http://www.huawei.com/",
            ATTR_UPNP_MODEL_NAME: "Huawei router",
            ATTR_UPNP_MODEL_NUMBER: "12345678",
            ATTR_UPNP_PRESENTATION_URL: url,
            ATTR_UPNP_UDN: "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            **upnp_data,
        },
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context=context,
        data=service_info,
    )

    for k, v in expected_result.items():
        assert result[k] == v  # type: ignore[literal-required] # expected is a subset
    if result.get("data_schema"):
        assert result["data_schema"] is not None
        assert result["data_schema"]({})[CONF_URL] == url + "/"

    if result["type"] is FlowResultType.ABORT:
        return

    login_requests_mock.request(
        ANY,
        f"{FIXTURE_USER_INPUT[CONF_URL]}api/user/login",
        text="<response>OK</response>",
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == service_info.upnp[ATTR_UPNP_MODEL_NAME]
    assert result["result"].data[CONF_UPNP_UDN] == service_info.upnp[ATTR_UPNP_UDN]