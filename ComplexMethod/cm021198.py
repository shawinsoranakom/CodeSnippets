async def test_async_remove_entry(
    hass: HomeAssistant,
    setup_integration: ComponentSetup,
) -> None:
    """Test async_remove_entry."""
    # Setup default config entry
    await setup_integration()

    # Setup additional config entry
    agent_id = ulid()
    private_key = create_private_key_file(hass)
    new_config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=agent_id,
        unique_id=agent_id,
        title="another@192.168.0.100",
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 22,
            CONF_USERNAME: "another",
            CONF_PASSWORD: "password",
            CONF_PRIVATE_KEY_FILE: str(private_key),
            CONF_BACKUP_LOCATION: "backup_location",
        },
    )
    new_config_entry.add_to_hass(hass)
    await setup_integration(new_config_entry)
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2

    config_entry = entries[0]
    private_key = Path(config_entry.data[CONF_PRIVATE_KEY_FILE])
    new_private_key = Path(new_config_entry.data[CONF_PRIVATE_KEY_FILE])

    # Make sure private keys from both configs exists
    assert private_key.parent == new_private_key.parent
    assert private_key.exists()
    assert new_private_key.exists()

    # Remove first config entry - the private key from second will still be in filesystem
    # as well as integration storage directory
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    assert not private_key.exists()
    assert new_private_key.exists()
    assert new_private_key.parent.exists()
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    # Remove the second config entry, ensuring all files and integration storage directory removed.
    assert await hass.config_entries.async_remove(new_config_entry.entry_id)
    assert not new_private_key.exists()
    assert not new_private_key.parent.exists()

    assert hass.config_entries.async_entries(DOMAIN) == []
    assert config_entry.state is ConfigEntryState.NOT_LOADED