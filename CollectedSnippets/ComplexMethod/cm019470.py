async def test_zeroconf_rediscover(
    hass: HomeAssistant,
    entry_domain: str,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
    entry_source: str,
) -> None:
    """Test we reinitiate flows when an ignored config entry is removed."""

    def http_only_service_update_mock(zeroconf, services, handlers):
        """Call service update handler."""
        handlers[0](
            zeroconf,
            "_http._tcp.local.",
            "Shelly108._http._tcp.local.",
            ServiceStateChange.Added,
        )

    entry = MockConfigEntry(
        domain=entry_domain,
        discovery_keys=entry_discovery_keys,
        unique_id="mock-unique-id",
        state=config_entries.ConfigEntryState.LOADED,
        source=entry_source,
    )
    entry.add_to_hass(hass)

    with (
        patch.dict(
            zc_gen.ZEROCONF,
            {
                "_http._tcp.local.": [
                    {
                        "domain": "shelly",
                        "name": "shelly*",
                        "properties": {"macaddress": "ffaadd*"},
                    }
                ]
            },
            clear=True,
        ),
        patch.object(hass.config_entries.flow, "async_init") as mock_config_flow,
        patch.object(
            discovery, "AsyncServiceBrowser", side_effect=http_only_service_update_mock
        ) as mock_service_browser,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceInfo",
            side_effect=get_zeroconf_info_mock("FFAADDCC11DD"),
        ),
    ):
        assert await async_setup_component(hass, zeroconf.DOMAIN, {zeroconf.DOMAIN: {}})
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        expected_context = {
            "discovery_key": DiscoveryKey(
                domain="zeroconf",
                key=("_http._tcp.local.", "Shelly108._http._tcp.local."),
                version=1,
            ),
            "source": "zeroconf",
        }
        assert len(mock_service_browser.mock_calls) == 1
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "shelly"
        assert mock_config_flow.mock_calls[0][2]["context"] == expected_context

        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()

        assert len(mock_service_browser.mock_calls) == 1
        assert len(mock_config_flow.mock_calls) == 2
        assert mock_config_flow.mock_calls[1][1][0] == "shelly"
        assert mock_config_flow.mock_calls[1][2]["context"] == expected_context