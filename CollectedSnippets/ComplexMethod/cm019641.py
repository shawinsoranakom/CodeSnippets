async def test_user_setup_fail(
    hass: HomeAssistant,
    device_id: str,
    connect_res: bool,
    mock_droplet_discovery: AsyncMock,
    mock_droplet_connection: AsyncMock,
    mock_droplet: AsyncMock,
) -> None:
    """Test user setup failing due to no device ID or failed connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result is not None
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    attrs = {
        "get_device_id.return_value": device_id,
        "try_connect.return_value": connect_res,
    }
    mock_droplet_discovery.configure_mock(**attrs)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE, CONF_IP_ADDRESS: MOCK_HOST},
    )
    assert result is not None
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": "cannot_connect"}

    # The user should be able to try again. Maybe the droplet was disconnected from the network or something
    attrs = {
        "get_device_id.return_value": MOCK_DEVICE_ID,
        "try_connect.return_value": True,
    }
    mock_droplet_discovery.configure_mock(**attrs)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE, CONF_IP_ADDRESS: MOCK_HOST},
    )
    assert result is not None
    assert result.get("type") is FlowResultType.CREATE_ENTRY