async def test_getting_existing_headers(
    mock_get_ssdp,
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_flow_init,
) -> None:
    """Test getting existing/previously scanned headers."""
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
    mock_ssdp_search_response = _ssdp_headers(
        {
            "ST": "mock-st",
            "LOCATION": "http://1.1.1.1",
            "USN": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
            "SERVER": "mock-server",
            "EXT": "",
            "_source": "search",
        }
    )
    ssdp_listener = await init_ssdp_component(hass)
    ssdp_listener._on_search(mock_ssdp_search_response)

    discovery_info_by_st = await ssdp.async_get_discovery_info_by_st(hass, "mock-st")
    discovery_info_by_st = discovery_info_by_st[0]
    assert discovery_info_by_st.ssdp_ext == ""
    assert discovery_info_by_st.ssdp_location == "http://1.1.1.1"
    assert discovery_info_by_st.ssdp_server == "mock-server"
    assert discovery_info_by_st.ssdp_st == "mock-st"
    assert (
        discovery_info_by_st.ssdp_usn
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3"
    )
    assert discovery_info_by_st.ssdp_udn == ANY
    assert discovery_info_by_st.ssdp_headers["_timestamp"] == ANY
    assert discovery_info_by_st.upnp == {
        ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
    }

    discovery_info_by_udn = await ssdp.async_get_discovery_info_by_udn(
        hass, "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL"
    )
    discovery_info_by_udn = discovery_info_by_udn[0]
    assert discovery_info_by_udn.ssdp_ext == ""
    assert discovery_info_by_udn.ssdp_location == "http://1.1.1.1"
    assert discovery_info_by_udn.ssdp_server == "mock-server"
    assert discovery_info_by_udn.ssdp_st == "mock-st"
    assert (
        discovery_info_by_udn.ssdp_usn
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3"
    )
    assert discovery_info_by_udn.ssdp_udn == ANY
    assert discovery_info_by_udn.ssdp_headers["_timestamp"] == ANY
    assert discovery_info_by_udn.upnp == {
        ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
    }

    discovery_info_by_udn_st = await ssdp.async_get_discovery_info_by_udn_st(
        hass, "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL", "mock-st"
    )
    assert discovery_info_by_udn_st.ssdp_ext == ""
    assert discovery_info_by_udn_st.ssdp_location == "http://1.1.1.1"
    assert discovery_info_by_udn_st.ssdp_server == "mock-server"
    assert discovery_info_by_udn_st.ssdp_st == "mock-st"
    assert (
        discovery_info_by_udn_st.ssdp_usn
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3"
    )
    assert discovery_info_by_udn_st.ssdp_udn == ANY
    assert discovery_info_by_udn_st.ssdp_headers["_timestamp"] == ANY
    assert discovery_info_by_udn_st.upnp == {
        ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
    }

    assert (
        await ssdp.async_get_discovery_info_by_udn_st(hass, "wrong", "mock-st") is None
    )