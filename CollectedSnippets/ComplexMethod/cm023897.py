async def test_user_setup_device_offline(hass: HomeAssistant, mock_device) -> None:
    """Test manually setting up when device is offline."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    mock_device.device_config.side_effect = DeviceConnectionError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCKED_DEVICE_IP_ADDRESS,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HOST: "cannot_connect"}
    assert result["step_id"] == "user"

    mock_device.device_config.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCKED_DEVICE_IP_ADDRESS,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY