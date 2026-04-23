async def test_discovery_auth(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test authenticated discovery."""
    mock_device = _mocked_device(
        alias=ALIAS,
        ip_address=IP_ADDRESS,
        mac=MAC_ADDRESS,
        device_config=DEVICE_CONFIG_KLAP,
        credentials_hash=CREDENTIALS_HASH_KLAP,
    )

    with override_side_effect(mock_connect["connect"], AuthenticationError):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS,
                CONF_MAC: MAC_ADDRESS,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: mock_device,
            },
        )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_auth_confirm"
    assert not result["errors"]

    with override_side_effect(mock_connect["connect"], lambda *_, **__: mock_device):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == DEFAULT_ENTRY_TITLE
    assert result2["data"] == CREATE_ENTRY_DATA_KLAP
    assert result2["context"]["unique_id"] == MAC_ADDRESS