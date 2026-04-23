async def test_move_credentials_hash(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test credentials hash moved to parent.

    As async_setup_entry will succeed the hash on the parent is updated
    from the device.
    """
    device_config = {
        **DEVICE_CONFIG_DICT_KLAP,
        "credentials_hash": "theHash",
    }
    entry_data = {**CREATE_ENTRY_DATA_KLAP, CONF_DEVICE_CONFIG: device_config}

    entry = MockConfigEntry(
        title="TPLink",
        domain=DOMAIN,
        data=entry_data,
        entry_id="123456",
        unique_id=MAC_ADDRESS,
        version=1,
        minor_version=3,
    )
    assert entry.data[CONF_DEVICE_CONFIG][CONF_CREDENTIALS_HASH] == "theHash"
    entry.add_to_hass(hass)

    async def _connect(config):
        config.credentials_hash = "theNewHash"
        return _mocked_device(device_config=config, credentials_hash="theNewHash")

    with (
        patch("homeassistant.components.tplink.Device.connect", new=_connect),
        patch("homeassistant.components.tplink.PLATFORMS", []),
        patch("homeassistant.components.tplink.CONF_CONFIG_ENTRY_MINOR_VERSION", 4),
        _patch_discovery(),
        _patch_single_discovery(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.minor_version == 4
    assert entry.state is ConfigEntryState.LOADED
    assert CONF_CREDENTIALS_HASH not in entry.data[CONF_DEVICE_CONFIG]
    assert CONF_CREDENTIALS_HASH in entry.data
    # Gets the new hash from the successful connection.
    assert entry.data[CONF_CREDENTIALS_HASH] == "theNewHash"
    assert "Migration to version 1.4 complete" in caplog.text