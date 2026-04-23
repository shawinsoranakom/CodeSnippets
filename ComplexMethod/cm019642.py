async def test_zeroconf_setup(
    hass: HomeAssistant,
    pre_normalized_code: str,
    normalized_code: str,
    mock_droplet_discovery: AsyncMock,
    mock_droplet: AsyncMock,
    mock_droplet_connection: AsyncMock,
) -> None:
    """Test successful setup of Droplet via zeroconf."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=IPv4Address(MOCK_HOST),
        ip_addresses=[IPv4Address(MOCK_HOST)],
        port=MOCK_PORT,
        hostname=MOCK_DEVICE_ID,
        type="_droplet._tcp.local.",
        name=MOCK_DEVICE_ID,
        properties={},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )
    assert result is not None
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_CODE: pre_normalized_code}
    )
    assert result is not None
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("data") == {
        CONF_DEVICE_ID: MOCK_DEVICE_ID,
        CONF_IP_ADDRESS: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
        CONF_CODE: normalized_code,
    }
    assert result.get("context") is not None
    assert result.get("context", {}).get("unique_id") == MOCK_DEVICE_ID