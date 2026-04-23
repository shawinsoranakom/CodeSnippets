async def test_zeroconf_no_encryption_key_via_dashboard(
    hass: HomeAssistant,
    mock_client: APIClient,
) -> None:
    """Test encryption key not retrieved from dashboard."""
    service_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.43.183"),
        ip_addresses=[ip_address("192.168.43.183")],
        hostname="test8266.local.",
        name="mock_name",
        port=6053,
        properties={
            "mac": "1122334455aa",
        },
        type="mock_type",
    )
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=service_info
    )

    assert flow["type"] is FlowResultType.FORM
    assert flow["step_id"] == "discovery_confirm"
    assert flow["description_placeholders"] == {"name": "test8266"}

    await dashboard.async_get_dashboard(hass).async_refresh()

    mock_client.device_info.side_effect = RequiresEncryptionAPIError

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encryption_key"
    assert result["description_placeholders"] == {"name": "test8266"}

    mock_client.device_info.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: VALID_NOISE_PSK}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "192.168.43.183",
        CONF_PORT: 6053,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: VALID_NOISE_PSK,
        CONF_DEVICE_NAME: "test",
    }
    assert mock_client.noise_psk == VALID_NOISE_PSK