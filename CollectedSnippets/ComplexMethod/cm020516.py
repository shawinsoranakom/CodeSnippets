async def test_integration_discovery_with_connection_change(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test that config entry is updated with new device config.

    And that connection_hash is removed as it will be invalid.
    """
    mock_config_entry = MockConfigEntry(
        title="TPLink",
        domain=DOMAIN,
        data=CREATE_ENTRY_DATA_AES,
        unique_id=MAC_ADDRESS2,
    )
    mock_config_entry.add_to_hass(hass)
    with (
        patch("homeassistant.components.tplink.Discover.discover", return_value={}),
        override_side_effect(mock_connect["connect"], KasaException()),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    assert (
        len(
            hass.config_entries.flow.async_progress_by_handler(
                DOMAIN, match_context={"source": SOURCE_REAUTH}
            )
        )
        == 0
    )
    assert mock_config_entry.data[CONF_HOST] == IP_ADDRESS2
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_AES.to_dict()
    )
    assert mock_config_entry.data[CONF_CREDENTIALS_HASH] == CREDENTIALS_HASH_AES

    mock_connect["connect"].reset_mock()
    NEW_DEVICE_CONFIG = {
        **DEVICE_CONFIG_DICT_KLAP,
        "connection_type": CONN_PARAMS_KLAP.to_dict(),
        CONF_HOST: IP_ADDRESS2,
    }
    config = DeviceConfig.from_dict(NEW_DEVICE_CONFIG)
    # Reset the connect mock so when the config flow reloads the entry it succeeds

    bulb = _mocked_device(
        device_config=config,
        mac=mock_config_entry.unique_id,
    )

    with (
        patch(
            "homeassistant.components.tplink.async_create_clientsession",
            return_value="Foo",
        ),
        override_side_effect(mock_connect["connect"], lambda *_, **__: bulb),
    ):
        discovery_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS2,
                CONF_MAC: MAC_ADDRESS2,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: bulb,
            },
        )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert discovery_result["type"] is FlowResultType.ABORT
    assert discovery_result["reason"] == "already_configured"
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_KLAP.to_dict()
    )
    assert mock_config_entry.data[CONF_HOST] == IP_ADDRESS2
    assert CREDENTIALS_HASH_AES not in mock_config_entry.data

    assert mock_config_entry.state is ConfigEntryState.LOADED

    config.host = IP_ADDRESS2
    config.http_client = "Foo"
    config.aes_keys = AES_KEYS
    mock_connect["connect"].assert_awaited_once_with(config=config)