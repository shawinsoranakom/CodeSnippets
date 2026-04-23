async def test_setup(hass: HomeAssistant, mock_async_zeroconf: MagicMock) -> None:
    """Test configured options for a device are loaded via config entry."""
    mock_zc = {
        "_http._tcp.local.": [
            {
                "domain": "shelly",
                "name": "shelly*",
                "properties": {"macaddress": "ffaadd*"},
            }
        ],
        "_Volumio._tcp.local.": [{"domain": "volumio"}],
    }
    with (
        patch.dict(
            zc_gen.ZEROCONF,
            mock_zc,
            clear=True,
        ),
        patch.object(hass.config_entries.flow, "async_init") as mock_config_flow,
        patch.object(
            discovery, "AsyncServiceBrowser", side_effect=service_update_mock
        ) as mock_service_browser,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceInfo",
            side_effect=get_service_info_mock,
        ),
    ):
        assert await async_setup_component(hass, zeroconf.DOMAIN, {zeroconf.DOMAIN: {}})
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    assert len(mock_service_browser.mock_calls) == 1
    expected_flow_calls = 0
    for matching_components in mock_zc.values():
        domains = set()
        for component in matching_components:
            if len(component) == 1:
                domains.add(component["domain"])
        expected_flow_calls += len(domains)
    assert len(mock_config_flow.mock_calls) == expected_flow_calls

    # Test instance is set.
    assert "zeroconf" in hass.data
    assert await zeroconf.async_get_async_instance(hass) is mock_async_zeroconf