async def test_user_flow_embedded_st(
    hass: HomeAssistant, domain_data_mock: Mock
) -> None:
    """Test user-init'd flow for device with an embedded DMR."""
    # Device is the wrong type
    upnp_device = domain_data_mock.upnp_factory.async_create_device.return_value
    upnp_device.udn = MOCK_ROOT_DEVICE_UDN
    upnp_device.device_type = "ROOT_DEVICE_TYPE"
    upnp_device.name = "ROOT_DEVICE_NAME"
    embedded_device = Mock(spec=UpnpDevice)
    embedded_device.udn = MOCK_DEVICE_UDN
    embedded_device.device_type = MOCK_DEVICE_TYPE
    embedded_device.name = MOCK_DEVICE_NAME
    embedded_device.services = upnp_device.services
    embedded_device.all_services = upnp_device.all_services
    upnp_device.services = {}
    upnp_device.all_services = []
    upnp_device.all_devices.append(embedded_device)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: MOCK_DEVICE_LOCATION}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DEVICE_NAME
    assert result["data"] == {
        CONF_URL: MOCK_DEVICE_LOCATION,
        CONF_DEVICE_ID: MOCK_DEVICE_UDN,
        CONF_TYPE: MOCK_DEVICE_TYPE,
        CONF_MAC: MOCK_MAC_ADDRESS,
    }
    assert result["options"] == {CONF_POLL_AVAILABILITY: True}