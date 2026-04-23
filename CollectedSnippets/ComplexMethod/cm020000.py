async def test_flow_ssdp_discovery(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that config flow for one discovered bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:80/",
            upnp={
                ATTR_UPNP_MANUFACTURER_URL: DECONZ_MANUFACTURERURL,
                ATTR_UPNP_SERIAL: BRIDGE_ID,
            },
        ),
        context={"source": SOURCE_SSDP},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0].get("context", {}).get("configuration_url") == "http://1.2.3.4:80"

    aioclient_mock.post(
        "http://1.2.3.4:80/api",
        json=[{"success": {"username": API_KEY}}],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == BRIDGE_ID
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_PORT: 80,
        CONF_API_KEY: API_KEY,
    }