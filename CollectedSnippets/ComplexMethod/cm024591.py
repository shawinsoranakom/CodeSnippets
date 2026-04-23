async def test_config_entry_migrations(
    hass: HomeAssistant, mock_dsm: MagicMock
) -> None:
    """Test if reauthentication flow is triggered."""
    with (
        patch(
            "homeassistant.components.synology_dsm.common.SynologyDSM",
            return_value=mock_dsm,
        ),
        patch("homeassistant.components.synology_dsm.PLATFORMS", return_value=[]),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SSL: USE_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
                CONF_MAC: MACS[0],
            },
            options={CONF_SCAN_INTERVAL: 30},
        )
        entry.add_to_hass(hass)

        assert CONF_VERIFY_SSL not in entry.data
        assert CONF_BACKUP_SHARE not in entry.options
        assert CONF_BACKUP_PATH not in entry.options

        assert await hass.config_entries.async_setup(entry.entry_id)

        assert entry.data[CONF_VERIFY_SSL] == DEFAULT_VERIFY_SSL
        assert CONF_SCAN_INTERVAL not in entry.options
        assert entry.options[CONF_BACKUP_SHARE] is None
        assert entry.options[CONF_BACKUP_PATH] is None