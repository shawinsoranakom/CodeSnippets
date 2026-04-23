async def test_manual_port_override(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_discovery: AsyncMock,
    host_str: str,
    host: str,
    port: int,
) -> None:
    """Test manually setup."""
    config = DeviceConfig(
        host,
        credentials=None,
        port_override=port,
        connection_type=CONN_PARAMS_KLAP,
    )
    mock_device = _mocked_device(
        alias=ALIAS,
        ip_address=host,
        mac=MAC_ADDRESS,
        device_config=config,
        credentials_hash=CREDENTIALS_HASH_KLAP,
    )

    with override_side_effect(
        mock_discovery["try_connect_all"], lambda *_, **__: mock_device
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    # side_effects to cause auth confirm as the port override usually only
    # works with direct connections.
    mock_discovery["discover_single"].side_effect = TimeoutError
    mock_connect["connect"].side_effect = AuthenticationError

    with override_side_effect(
        mock_discovery["try_connect_all"], lambda *_, **__: mock_device
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: host_str}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user_auth_confirm"
    assert not result2["errors"]

    creds = Credentials("fake_username", "fake_password")
    with override_side_effect(
        mock_discovery["try_connect_all"], lambda *_, **__: mock_device
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )
    await hass.async_block_till_done()
    mock_discovery["try_connect_all"].assert_called_once_with(
        host, credentials=creds, port=port, http_client=ANY
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == DEFAULT_ENTRY_TITLE
    assert result3["data"] == {
        **CREATE_ENTRY_DATA_KLAP,
        CONF_PORT: port,
        CONF_HOST: host,
    }
    assert result3["context"]["unique_id"] == MAC_ADDRESS