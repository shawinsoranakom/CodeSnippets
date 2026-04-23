async def test_form_ssdp(hass: HomeAssistant) -> None:
    """Test we get the form with ssdp source."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://192.168.208.1:41417/rootDesc.xml",
            upnp={
                "friendlyName": "UniFi Dream Machine",
                "modelDescription": "UniFi Dream Machine Pro",
                "serialNumber": "e0:63:da:20:14:a9",
            },
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    assert (
        flows[0].get("context", {}).get("configuration_url")
        == "https://192.168.208.1:443"
    )

    context = next(
        flow["context"]
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert context["title_placeholders"] == {
        "host": "192.168.208.1",
        "site": "default",
    }