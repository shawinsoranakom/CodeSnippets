async def test_discovery_from_advertisement_sets_ssdp_st(
    mock_get_ssdp,
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_flow_init,
) -> None:
    """Test discovery from advertisement sets `ssdp_st` for more compatibility."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>
  <device>
    <deviceType>Paulus</deviceType>
  </device>
</root>
    """,
    )
    ssdp_listener = await init_ssdp_component(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    mock_ssdp_advertisement = _ssdp_headers(
        {
            "nt": "mock-st",
            "nts": "ssdp:alive",
            "location": "http://1.1.1.1",
            "usn": "uuid:mock-udn::mock-st",
            "_source": "advertisement",
        }
    )
    ssdp_listener._on_alive(mock_ssdp_advertisement)
    await hass.async_block_till_done()

    discovery_info = await ssdp.async_get_discovery_info_by_udn(hass, "uuid:mock-udn")
    discovery_info = discovery_info[0]
    assert discovery_info.ssdp_location == "http://1.1.1.1"
    assert discovery_info.ssdp_nt == "mock-st"
    # Set by ssdp component, not in original advertisement.
    assert discovery_info.ssdp_st == "mock-st"
    assert discovery_info.ssdp_usn == "uuid:mock-udn::mock-st"
    assert discovery_info.ssdp_udn == ANY
    assert discovery_info.ssdp_headers["nts"] == "ssdp:alive"
    assert discovery_info.ssdp_headers["_timestamp"] == ANY
    assert discovery_info.upnp == {
        ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ATTR_UPNP_UDN: "uuid:mock-udn",
    }