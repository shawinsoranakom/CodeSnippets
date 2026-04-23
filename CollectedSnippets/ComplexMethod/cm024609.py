async def test_options_flow(
    hass: HomeAssistant, service_with_filestation: MagicMock
) -> None:
    """Test config flow options."""
    with (
        patch(
            "homeassistant.components.synology_dsm.common.SynologyDSM",
            return_value=service_with_filestation,
        ),
        patch("homeassistant.components.synology_dsm.PLATFORMS", return_value=[]),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SSL: USE_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
                CONF_MAC: MACS[0],
            },
            unique_id=SERIAL,
        )
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.options == {CONF_BACKUP_SHARE: None, CONF_BACKUP_PATH: None}

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SNAPSHOT_QUALITY: 0,
            CONF_BACKUP_PATH: "my_nackup_path",
            CONF_BACKUP_SHARE: "/ha_backup",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_SNAPSHOT_QUALITY] == 0
    assert config_entry.options[CONF_BACKUP_PATH] == "my_nackup_path"
    assert config_entry.options[CONF_BACKUP_SHARE] == "/ha_backup"