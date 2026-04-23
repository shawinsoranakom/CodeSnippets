async def test_reauth_update_with_encryption_change(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test reauth flow."""

    mock_config_entry = MockConfigEntry(
        title="TPLink",
        domain=DOMAIN,
        data={**CREATE_ENTRY_DATA_AES},
        unique_id=MAC_ADDRESS2,
    )
    mock_config_entry.add_to_hass(hass)
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_AES.to_dict()
    )
    assert mock_config_entry.data[CONF_CREDENTIALS_HASH] == CREDENTIALS_HASH_AES

    with (
        patch("homeassistant.components.tplink.Discover.discover", return_value={}),
        override_side_effect(mock_connect["connect"], AuthenticationError()),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    caplog.set_level(logging.DEBUG)
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    [result] = flows
    assert result["step_id"] == "reauth_confirm"
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_AES.to_dict()
    )
    assert CONF_CREDENTIALS_HASH not in mock_config_entry.data

    new_config = DeviceConfig(
        IP_ADDRESS2,
        credentials=None,
        connection_type=Device.ConnectionParameters(
            Device.Family.SmartTapoPlug, Device.EncryptionType.Klap
        ),
    )
    mock_device = _mocked_device(
        alias="my_device",
        ip_address=IP_ADDRESS2,
        mac=MAC_ADDRESS2,
        device_config=new_config,
        credentials_hash=CREDENTIALS_HASH_KLAP,
    )

    with (
        override_side_effect(
            mock_discovery["discover_single"], lambda *_, **__: mock_device
        ),
        override_side_effect(mock_connect["connect"], lambda *_, **__: mock_device),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )
        await hass.async_block_till_done(wait_background_tasks=True)
    assert "Connection type changed for 127.0.0.2" in caplog.text
    credentials = Credentials("fake_username", "fake_password")
    mock_discovery["discover_single"].assert_called_once_with(
        IP_ADDRESS2, credentials=credentials, port=None
    )
    mock_device.update.assert_called_once_with()
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_KLAP.to_dict()
    )
    assert mock_config_entry.data[CONF_HOST] == IP_ADDRESS2
    assert mock_config_entry.data[CONF_CREDENTIALS_HASH] == CREDENTIALS_HASH_KLAP