async def test_discovery_auth_camera(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test authenticated discovery for camera with stream."""
    mock_device = _mocked_device(
        alias=ALIAS_CAMERA,
        ip_address=IP_ADDRESS3,
        mac=MAC_ADDRESS3,
        model=MODEL_CAMERA,
        device_config=DEVICE_CONFIG_AES_CAMERA,
        credentials_hash=CREDENTIALS_HASH_AES,
        modules=[Module.Camera],
    )

    with override_side_effect(mock_connect["connect"], AuthenticationError):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS3,
                CONF_MAC: MAC_ADDRESS3,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: mock_device,
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_auth_confirm"
    assert not result["errors"]

    with override_side_effect(mock_connect["connect"], lambda *_, **__: mock_device):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "camera_auth_confirm"
    assert not result["errors"]

    with patch(
        "homeassistant.components.stream.async_check_stream_client_error",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LIVE_VIEW: True,
                CONF_USERNAME: "camuser",
                CONF_PASSWORD: "campass",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_ENTRY_TITLE_CAMERA
    assert result["data"] == CREATE_ENTRY_DATA_AES_CAMERA
    assert result["context"]["unique_id"] == MAC_ADDRESS3