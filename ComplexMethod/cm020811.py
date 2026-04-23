async def test_scan_with_registered_callback(
    mock_get_ssdp,
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test matching based on callback."""
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
            "st": "mock-st",
            "location": "http://1.1.1.1",
            "usn": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::mock-st",
            "server": "mock-server",
            "x-rincon-bootseq": "55",
            "ext": "",
            "_source": "search",
        }
    )
    ssdp_listener = await init_ssdp_component(hass)

    async_exception_callback = AsyncMock(side_effect=ValueError)
    await ssdp.async_register_callback(hass, async_exception_callback, {})

    async_integration_callback = AsyncMock()
    await ssdp.async_register_callback(
        hass, async_integration_callback, {"st": "mock-st"}
    )

    async_integration_match_all_callback = AsyncMock()
    await ssdp.async_register_callback(
        hass, async_integration_match_all_callback, {"x-rincon-bootseq": MATCH_ALL}
    )

    async_integration_match_all_not_present_callback = AsyncMock()
    await ssdp.async_register_callback(
        hass,
        async_integration_match_all_not_present_callback,
        {"x-not-there": MATCH_ALL},
    )

    async_not_matching_integration_callback = AsyncMock()
    await ssdp.async_register_callback(
        hass, async_not_matching_integration_callback, {"st": "not-match-mock-st"}
    )

    async_match_any_callback = AsyncMock()
    await ssdp.async_register_callback(hass, async_match_any_callback)

    await hass.async_block_till_done(wait_background_tasks=True)
    ssdp_listener._on_search(mock_ssdp_search_response)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert async_integration_callback.call_count == 1
    assert async_integration_match_all_callback.call_count == 1
    assert async_integration_match_all_not_present_callback.call_count == 0
    assert async_match_any_callback.call_count == 1
    assert async_not_matching_integration_callback.call_count == 0
    assert async_integration_callback.call_args[0][1] == ssdp.SsdpChange.ALIVE
    mock_call_data: SsdpServiceInfo = async_integration_callback.call_args[0][0]
    assert mock_call_data.ssdp_ext == ""
    assert mock_call_data.ssdp_location == "http://1.1.1.1"
    assert mock_call_data.ssdp_server == "mock-server"
    assert mock_call_data.ssdp_st == "mock-st"
    assert (
        mock_call_data.ssdp_usn == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::mock-st"
    )
    assert mock_call_data.ssdp_headers["x-rincon-bootseq"] == "55"
    assert mock_call_data.ssdp_udn == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL"
    assert mock_call_data.ssdp_headers["_timestamp"] == ANY
    assert mock_call_data.x_homeassistant_matching_domains == set()
    assert mock_call_data.upnp == {
        ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
    }
    assert "Exception in SSDP callback" in caplog.text

    async_integration_callback_from_cache = AsyncMock()
    await ssdp.async_register_callback(
        hass, async_integration_callback_from_cache, {"st": "mock-st"}
    )
    assert async_integration_callback_from_cache.call_count == 1