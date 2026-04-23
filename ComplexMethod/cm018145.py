async def test_ssdp(
    hass: HomeAssistant, mock_syncthru: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test SSDP discovery initiates config properly."""

    url = "http://192.168.1.2/"
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://192.168.1.2:5200/Printer.xml",
            upnp={
                ATTR_UPNP_DEVICE_TYPE: "urn:schemas-upnp-org:device:Printer:1",
                ATTR_UPNP_MANUFACTURER: "Samsung Electronics",
                ATTR_UPNP_PRESENTATION_URL: url,
                ATTR_UPNP_SERIAL: "00000000",
                ATTR_UPNP_UDN: "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            },
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert CONF_URL in result["data_schema"].schema
    for k in result["data_schema"].schema:
        if k == CONF_URL:
            assert k.default() == url

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: url, CONF_NAME: "Printer"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_URL: url, CONF_NAME: "Printer"}
    assert result["result"].unique_id == "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"