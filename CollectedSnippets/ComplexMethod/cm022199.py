async def test_ssdp_missing_services(hass: HomeAssistant) -> None:
    """Test SSDP ignores devices that are missing required services."""
    # No service list at all
    discovery = dataclasses.replace(MOCK_DISCOVERY)
    discovery.upnp = dict(discovery.upnp)
    del discovery.upnp[ATTR_UPNP_SERVICE_LIST]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=discovery,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_dms"

    # Service list does not contain services
    discovery = dataclasses.replace(MOCK_DISCOVERY)
    discovery.upnp = dict(discovery.upnp)
    discovery.upnp[ATTR_UPNP_SERVICE_LIST] = {"bad_key": "bad_value"}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=discovery,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_dms"

    # ContentDirectory service is missing
    discovery = dataclasses.replace(MOCK_DISCOVERY)
    discovery.upnp = dict(discovery.upnp)
    discovery.upnp[ATTR_UPNP_SERVICE_LIST] = {
        "service": [
            service
            for service in discovery.upnp[ATTR_UPNP_SERVICE_LIST]["service"]
            if service.get("serviceId") != "urn:upnp-org:serviceId:ContentDirectory"
        ]
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=discovery
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_dms"