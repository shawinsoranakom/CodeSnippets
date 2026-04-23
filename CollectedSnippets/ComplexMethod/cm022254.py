async def test_migrate_config_entry(
    hass: HomeAssistant,
    mock_fyta_connector: AsyncMock,
) -> None:
    """Test successful migration of entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    assert entry.version == 1
    assert entry.minor_version == 1

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 1
    assert entry.minor_version == 2
    assert entry.data[CONF_USERNAME] == USERNAME
    assert entry.data[CONF_PASSWORD] == PASSWORD
    assert entry.data[CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert entry.data[CONF_EXPIRATION] == EXPIRATION