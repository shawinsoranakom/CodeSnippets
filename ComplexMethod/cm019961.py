async def test_zeroconf(hass: HomeAssistant, mock_solarman: AsyncMock) -> None:
    """Test zeroconf discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            name="mock_name",
            port=8080,
            hostname="mock_hostname",
            type="_solarman._tcp.local.",
            properties={
                "product_type": "SP-2W-EU",
                "serial": TEST_DEVICE_SN,
            },
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{MODEL_NAME_MAP[TEST_MODEL]} ({TEST_HOST})"

    data = result["data"]
    assert data[CONF_HOST] == TEST_HOST
    assert data[CONF_SN] == TEST_DEVICE_SN
    assert data[CONF_MODEL] == TEST_MODEL
    assert result["context"]["unique_id"] == TEST_DEVICE_SN