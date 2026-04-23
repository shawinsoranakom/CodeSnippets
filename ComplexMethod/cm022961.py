async def test_migrate_entry_v1_with_ignored_duplicates(
    hass: HomeAssistant, config_entry_v1: MockConfigEntry
) -> None:
    """Remove ignored entries with the same MAC and then migrate."""
    config_entry_v1.add_to_hass(hass)

    ignored_1 = MockConfigEntry(
        domain=DOMAIN,
        title="Ignored 1",
        unique_id="aabbccddeeff",
        source=SOURCE_IGNORE,
        version=1,
        minor_version=0,
        data={"host": "wled-ignored-1.local"},
    )
    ignored_2 = MockConfigEntry(
        domain=DOMAIN,
        title="Ignored 2",
        unique_id="aabbccddeeff",
        source=SOURCE_IGNORE,
        version=1,
        minor_version=0,
        data={"host": "wled-ignored-2.local"},
    )

    ignored_1.add_to_hass(hass)
    ignored_2.add_to_hass(hass)

    result = await hass.config_entries.async_setup(config_entry_v1.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert config_entry_v1.state == ConfigEntryState.LOADED
    assert config_entry_v1.version == 1
    assert config_entry_v1.minor_version == 2
    assert config_entry_v1.unique_id == "aabbccddeeff"

    assert ignored_1.state is ConfigEntryState.NOT_LOADED
    assert ignored_2.state is ConfigEntryState.NOT_LOADED