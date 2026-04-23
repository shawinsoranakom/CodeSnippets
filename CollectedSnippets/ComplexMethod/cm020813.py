async def test_ssdp_rediscover(
    mock_get_ssdp,
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_flow_init,
    entry_domain: str,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
    entry_source: str,
) -> None:
    """Test we reinitiate flows when an ignored config entry is removed."""
    entry = MockConfigEntry(
        domain=entry_domain,
        discovery_keys=entry_discovery_keys,
        unique_id="mock-unique-id",
        state=config_entries.ConfigEntryState.LOADED,
        source=entry_source,
    )
    entry.add_to_hass(hass)

    mock_ssdp_search_response = _ssdp_headers(
        {
            "st": "mock-st",
            "location": "http://1.1.1.1",
            "usn": "uuid:mock-udn::mock-st",
            "server": "mock-server",
            "ext": "",
            "_source": "search",
        }
    )
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>
  <device>
    <deviceType>Paulus</deviceType>
    <manufacturer>Paulus</manufacturer>
  </device>
</root>
    """,
    )
    ssdp_listener = await init_ssdp_component(hass)
    ssdp_listener._on_search(mock_ssdp_search_response)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    expected_context = {
        "discovery_key": DiscoveryKey(domain="ssdp", key="uuid:mock-udn", version=1),
        "source": config_entries.SOURCE_SSDP,
    }
    assert len(mock_flow_init.mock_calls) == 1
    assert mock_flow_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_flow_init.mock_calls[0][2]["context"] == expected_context
    mock_call_data: SsdpServiceInfo = mock_flow_init.mock_calls[0][2]["data"]
    assert mock_call_data.ssdp_st == "mock-st"
    assert mock_call_data.ssdp_location == "http://1.1.1.1"

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert len(mock_flow_init.mock_calls) == 2
    assert mock_flow_init.mock_calls[1][1][0] == "mock-domain"
    assert mock_flow_init.mock_calls[1][2]["context"] == expected_context
    assert (
        mock_flow_init.mock_calls[1][2]["data"]
        == mock_flow_init.mock_calls[0][2]["data"]
    )