async def test_migration_1_2(hass: HomeAssistant, mock_pyairvisual) -> None:
    """Test migrating from version 1 to 2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_API_KEY,
        data={
            CONF_API_KEY: TEST_API_KEY,
            CONF_GEOGRAPHIES: [
                {
                    CONF_LATITUDE: TEST_LATITUDE,
                    CONF_LONGITUDE: TEST_LONGITUDE,
                },
                {
                    CONF_CITY: TEST_CITY,
                    CONF_STATE: TEST_STATE,
                    CONF_COUNTRY: TEST_COUNTRY,
                },
                {
                    CONF_LATITUDE: TEST_LATITUDE2,
                    CONF_LONGITUDE: TEST_LONGITUDE2,
                },
            ],
        },
        version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 3

    # Ensure that after migration, each configuration has its own config entry:
    identifier1 = f"{TEST_LATITUDE}, {TEST_LONGITUDE}"
    assert config_entries[0].unique_id == identifier1
    assert config_entries[0].title == f"Cloud API ({identifier1})"
    assert config_entries[0].data == {
        **COORDS_CONFIG,
        CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    }

    identifier2 = f"{TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY}"
    assert config_entries[1].unique_id == identifier2
    assert config_entries[1].title == f"Cloud API ({identifier2})"
    assert config_entries[1].data == {
        **NAME_CONFIG,
        CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_NAME,
    }

    identifier3 = f"{TEST_LATITUDE2}, {TEST_LONGITUDE2}"
    assert config_entries[2].unique_id == identifier3
    assert config_entries[2].title == f"Cloud API ({identifier3})"
    assert config_entries[2].data == {
        **COORDS_CONFIG2,
        CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    }