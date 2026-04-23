async def test_migrate_remove_device_config(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_discovery: AsyncMock,
    caplog: pytest.LogCaptureFixture,
    device_config: DeviceConfig,
    expected_entry_data: dict[str, Any],
    credentials_hash: str,
) -> None:
    """Test credentials hash moved to parent.

    As async_setup_entry will succeed the hash on the parent is updated
    from the device.
    """
    old_device_config = {
        k: v for k, v in device_config.to_dict().items() if k != "credentials"
    }
    device_config_dict = {
        **old_device_config,
        "uses_http": device_config.connection_type.encryption_type
        is not Device.EncryptionType.Xor,
    }

    OLD_CREATE_ENTRY_DATA = {
        CONF_HOST: expected_entry_data[CONF_HOST],
        CONF_ALIAS: ALIAS,
        CONF_MODEL: MODEL,
        CONF_DEVICE_CONFIG: device_config_dict,
    }

    entry = MockConfigEntry(
        title="TPLink",
        domain=DOMAIN,
        data=OLD_CREATE_ENTRY_DATA,
        entry_id="123456",
        unique_id=MAC_ADDRESS,
        version=1,
        minor_version=4,
    )
    entry.add_to_hass(hass)

    async def _connect(config):
        config.credentials_hash = credentials_hash
        config.aes_keys = expected_entry_data.get(CONF_AES_KEYS)
        return _mocked_device(device_config=config, credentials_hash=credentials_hash)

    with (
        patch("homeassistant.components.tplink.Device.connect", new=_connect),
        patch("homeassistant.components.tplink.PLATFORMS", []),
        patch(
            "homeassistant.components.tplink.async_create_clientsession",
            return_value="Foo",
        ),
        patch("homeassistant.components.tplink.CONF_CONFIG_ENTRY_MINOR_VERSION", 5),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.minor_version == 5
    assert entry.state is ConfigEntryState.LOADED
    assert CONF_DEVICE_CONFIG not in entry.data
    assert entry.data == expected_entry_data

    assert "Migration to version 1.5 complete" in caplog.text