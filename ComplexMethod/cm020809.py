async def test_ssdp_flow_dispatched_on_manufacturer_url(
    mock_get_ssdp,
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    mock_flow_init,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test matching based on manufacturerURL."""
    mock_ssdp_search_response = _ssdp_headers(
        {
            "st": "mock-st",
            "manufacturerURL": "mock-url",
            "location": "http://1.1.1.1",
            "usn": "uuid:mock-udn::mock-st",
            "server": "mock-server",
            "ext": "",
            "_source": "search",
        }
    )
    ssdp_listener = await init_ssdp_component(hass)
    ssdp_listener._on_search(mock_ssdp_search_response)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert len(mock_flow_init.mock_calls) == 1
    assert mock_flow_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_flow_init.mock_calls[0][2]["context"] == {
        "discovery_key": DiscoveryKey(domain="ssdp", key="uuid:mock-udn", version=1),
        "source": config_entries.SOURCE_SSDP,
    }
    mock_call_data: SsdpServiceInfo = mock_flow_init.mock_calls[0][2]["data"]
    assert mock_call_data.ssdp_st == "mock-st"
    assert mock_call_data.ssdp_location == "http://1.1.1.1"
    assert mock_call_data.ssdp_usn == "uuid:mock-udn::mock-st"
    assert mock_call_data.ssdp_server == "mock-server"
    assert mock_call_data.ssdp_ext == ""
    assert mock_call_data.ssdp_udn == ANY
    assert mock_call_data.ssdp_headers["_timestamp"] == ANY
    assert mock_call_data.x_homeassistant_matching_domains == {"mock-domain"}
    assert mock_call_data.upnp == {ATTR_UPNP_UDN: "uuid:mock-udn"}
    assert "Failed to fetch ssdp data" not in caplog.text