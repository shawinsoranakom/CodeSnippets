async def test_ssdp_ignore_device(hass: HomeAssistant) -> None:
    """Test SSDP discovery ignores certain devices."""
    discovery = dataclasses.replace(MOCK_DISCOVERY)
    discovery.x_homeassistant_matching_domains = {DOMAIN, "other_domain"}
    assert discovery.x_homeassistant_matching_domains
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=discovery,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "alternative_integration"

    discovery = dataclasses.replace(MOCK_DISCOVERY)
    discovery.upnp = dict(discovery.upnp)
    discovery.upnp[ATTR_UPNP_DEVICE_TYPE] = "urn:schemas-upnp-org:device:ZonePlayer:1"
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=discovery,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "alternative_integration"

    for manufacturer, model in (
        ("XBMC Foundation", "Kodi"),
        ("Samsung", "Smart TV"),
        ("LG Electronics.", "LG TV"),
        ("Royal Philips Electronics", "Philips TV DMR"),
    ):
        discovery = dataclasses.replace(MOCK_DISCOVERY)
        discovery.upnp = dict(discovery.upnp)
        discovery.upnp[ATTR_UPNP_MANUFACTURER] = manufacturer
        discovery.upnp[ATTR_UPNP_MODEL_NAME] = model
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=discovery,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "alternative_integration"