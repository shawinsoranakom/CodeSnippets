async def test_user_setup(
    hass: HomeAssistant,
    pre_normalized_code: str,
    normalized_code: str,
    mock_droplet_discovery: AsyncMock,
    mock_droplet_connection: AsyncMock,
    mock_droplet: AsyncMock,
) -> None:
    """Test successful Droplet user setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result is not None
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: pre_normalized_code, CONF_IP_ADDRESS: "192.168.1.2"},
    )
    assert result is not None
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("data") == {
        CONF_CODE: normalized_code,
        CONF_DEVICE_ID: MOCK_DEVICE_ID,
        CONF_IP_ADDRESS: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }
    assert result.get("context") is not None
    assert result.get("context", {}).get("unique_id") == MOCK_DEVICE_ID