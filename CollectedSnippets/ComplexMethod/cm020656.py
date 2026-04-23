async def test_migrate_entry_v1_to_v2_3(hass: HomeAssistant) -> None:
    """Test successful migration of entry data from v1 to v2.3."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data=MOCK_CONFIG,
        options={
            CONF_REALTIME: DEFAULT_REALTIME,
            CONF_VEHICLE_TYPE: DEFAULT_VEHICLE_TYPE,
            CONF_UNITS: METRIC_UNITS,
            CONF_AVOID_FERRIES: DEFAULT_AVOID_FERRIES,
            CONF_AVOID_SUBSCRIPTION_ROADS: DEFAULT_AVOID_SUBSCRIPTION_ROADS,
            CONF_AVOID_TOLL_ROADS: DEFAULT_AVOID_TOLL_ROADS,
        },
    )

    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    updated_entry = hass.config_entries.async_get_entry(mock_entry.entry_id)

    assert updated_entry.state is ConfigEntryState.LOADED
    assert updated_entry.version == 2
    assert updated_entry.minor_version == 3
    assert updated_entry.options[CONF_INCL_FILTER] == DEFAULT_FILTER
    assert updated_entry.options[CONF_EXCL_FILTER] == DEFAULT_FILTER
    assert updated_entry.options[CONF_TIME_DELTA] == DEFAULT_TIME_DELTA
    assert updated_entry.options[CONF_BASE_COORDINATES] == {
        CONF_LATITUDE: 40.713,
        CONF_LONGITUDE: -74.006,
    }

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data=MOCK_CONFIG,
        options={
            CONF_REALTIME: DEFAULT_REALTIME,
            CONF_VEHICLE_TYPE: DEFAULT_VEHICLE_TYPE,
            CONF_UNITS: METRIC_UNITS,
            CONF_AVOID_FERRIES: DEFAULT_AVOID_FERRIES,
            CONF_AVOID_SUBSCRIPTION_ROADS: DEFAULT_AVOID_SUBSCRIPTION_ROADS,
            CONF_AVOID_TOLL_ROADS: DEFAULT_AVOID_TOLL_ROADS,
            CONF_INCL_FILTER: "IncludeThis",
            CONF_EXCL_FILTER: "ExcludeThis",
        },
    )

    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    updated_entry = hass.config_entries.async_get_entry(mock_entry.entry_id)

    assert updated_entry.state is ConfigEntryState.LOADED
    assert updated_entry.version == 2
    assert updated_entry.minor_version == 3
    assert updated_entry.options[CONF_INCL_FILTER] == ["IncludeThis"]
    assert updated_entry.options[CONF_EXCL_FILTER] == ["ExcludeThis"]
    assert updated_entry.options[CONF_TIME_DELTA] == DEFAULT_TIME_DELTA
    assert updated_entry.options[CONF_BASE_COORDINATES] == {
        CONF_LATITUDE: 40.713,
        CONF_LONGITUDE: -74.006,
    }