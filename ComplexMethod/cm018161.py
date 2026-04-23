async def test_device_registry_info_update_contact(
    hass: HomeAssistant,
    voip_devices: VoIPDevices,
    call_info: CallInfo,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test info in device registry."""
    voip_device = voip_devices.async_get_or_create(call_info)
    assert not voip_device.async_allow_call(hass)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, call_info.caller_endpoint.uri)}
    )
    assert device is not None
    assert device.name == call_info.caller_endpoint.host
    assert device.manufacturer == "Grandstream"
    assert device.model == "HT801"
    assert device.sw_version == "1.0.17.5"

    # Test we update the device if the fw updates
    call_info.headers["user-agent"] = "Grandstream HT801 2.0.0.0"
    call_info.contact_endpoint = SipEndpoint("Test <sip:example.com:5061>")
    voip_device = voip_devices.async_get_or_create(call_info)

    assert voip_device.contact == SipEndpoint("Test <sip:example.com:5061>")
    assert not voip_device.async_allow_call(hass)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, call_info.caller_endpoint.uri)}
    )
    assert device.sw_version == "2.0.0.0"