async def test_zeroconf_encryption_key_via_dashboard_with_api_encryption_prop(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_dashboard: dict[str, Any],
) -> None:
    """Test encryption key retrieved from dashboard with api_encryption property set."""
    service_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.43.183"),
        ip_addresses=[ip_address("192.168.43.183")],
        hostname="test8266.local.",
        name="mock_name",
        port=6053,
        properties={
            "mac": "1122334455aa",
            "api_encryption": "any",
        },
        type="mock_type",
    )
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=service_info
    )

    assert flow["type"] is FlowResultType.FORM
    assert flow["step_id"] == "discovery_confirm"
    assert flow["description_placeholders"] == {"name": "test8266"}

    mock_dashboard["configured"].append(
        {
            "name": "test8266",
            "configuration": "test8266.yaml",
        }
    )

    await dashboard.async_get_dashboard(hass).async_refresh()

    mock_client.device_info.side_effect = [
        DeviceInfo(
            uses_password=False,
            name="test8266",
            mac_address="11:22:33:44:55:AA",
        ),
    ]

    with patch(
        "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_encryption_key",
        return_value=VALID_NOISE_PSK,
    ) as mock_get_encryption_key:
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], user_input={}
        )

    assert len(mock_get_encryption_key.mock_calls) == 1

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test8266"
    assert result["data"][CONF_HOST] == "192.168.43.183"
    assert result["data"][CONF_PORT] == 6053
    assert result["data"][CONF_NOISE_PSK] == VALID_NOISE_PSK

    assert result["result"]
    assert result["result"].unique_id == "11:22:33:44:55:aa"

    assert mock_client.noise_psk == VALID_NOISE_PSK