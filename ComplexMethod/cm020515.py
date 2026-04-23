async def test_integration_discovery_with_ip_change(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test integration updates ip address from discovery."""
    mock_config_entry.add_to_hass(hass)
    with (
        patch("homeassistant.components.tplink.Discover.discover", return_value={}),
        override_side_effect(mock_connect["connect"], KasaException()),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 0
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS]
        == CONN_PARAMS_LEGACY.to_dict()
    )
    assert mock_config_entry.data[CONF_HOST] == IP_ADDRESS

    mocked_device = _mocked_device(device_config=DEVICE_CONFIG_KLAP)
    with override_side_effect(mock_connect["connect"], lambda *_, **__: mocked_device):
        discovery_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS2,
                CONF_MAC: MAC_ADDRESS,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: mocked_device,
            },
        )
    await hass.async_block_till_done()
    assert discovery_result["type"] is FlowResultType.ABORT
    assert discovery_result["reason"] == "already_configured"
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_KLAP.to_dict()
    )
    assert mock_config_entry.data[CONF_HOST] == IP_ADDRESS2

    config = DeviceConfig.from_dict(DEVICE_CONFIG_DICT_KLAP)

    # Do a reload here and check that the
    # new config is picked up in setup_entry
    mock_connect["connect"].reset_mock(side_effect=True)
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
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    # Check that init set the new host correctly before calling connect
    assert config.host == IP_ADDRESS
    config.host = IP_ADDRESS2
    config.http_client = "Foo"
    mock_connect["connect"].assert_awaited_once_with(config=config)