async def test_migration_from_v1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test migration from version 1 to version 2."""
    # Create a v1 config entry with conversation options and an entity
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "1234", CONF_STATION_NUMBER: 4584},
        version=1,
        unique_id="4584",
        title="de Jongweg, Utrecht",
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "1234", CONF_STATION_NUMBER: 4585},
        version=1,
        unique_id="4585",
        title="Not de Jongweg, Utrecht",
    )
    mock_config_entry_2.add_to_hass(hass)

    device_1 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "4584")},
        name="de Jongweg, Utrecht",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "4584_air_quality",
        config_entry=mock_config_entry,
        device_id=device_1.id,
        suggested_object_id="de_jongweg_utrecht",
    )

    device_2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_2.entry_id,
        identifiers={(DOMAIN, "4585")},
        name="Not de Jongweg, Utrecht",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "4585_air_quality",
        config_entry=mock_config_entry_2,
        device_id=device_2.id,
        suggested_object_id="not_de_jongweg_utrecht",
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.version == 2
    assert entry.minor_version == 1
    assert not entry.options
    assert entry.title == "WAQI"
    assert len(entry.subentries) == 2

    subentry = list(entry.subentries.values())[0]
    assert subentry.subentry_type == "station"
    assert subentry.data[CONF_STATION_NUMBER] == 4584
    assert subentry.unique_id == "4584"
    assert subentry.title == "de Jongweg, Utrecht"

    entity = entity_registry.async_get("sensor.de_jongweg_utrecht")
    assert entity.unique_id == "4584_air_quality"
    assert entity.config_subentry_id == subentry.subentry_id
    assert entity.config_entry_id == entry.entry_id

    assert (device := device_registry.async_get_device(identifiers={(DOMAIN, "4584")}))
    assert device.identifiers == {(DOMAIN, "4584")}
    assert device.id == device_1.id
    assert device.config_entries == {mock_config_entry.entry_id}
    assert device.config_entries_subentries == {
        mock_config_entry.entry_id: {subentry.subentry_id}
    }

    subentry = list(entry.subentries.values())[1]
    assert subentry.subentry_type == "station"
    assert subentry.data[CONF_STATION_NUMBER] == 4585
    assert subentry.unique_id == "4585"
    assert subentry.title == "Not de Jongweg, Utrecht"

    entity = entity_registry.async_get("sensor.not_de_jongweg_utrecht")
    assert entity.unique_id == "4585_air_quality"
    assert entity.config_subentry_id == subentry.subentry_id
    assert entity.config_entry_id == entry.entry_id
    assert (device := device_registry.async_get_device(identifiers={(DOMAIN, "4585")}))
    assert device.identifiers == {(DOMAIN, "4585")}
    assert device.id == device_2.id
    assert device.config_entries == {mock_config_entry.entry_id}
    assert device.config_entries_subentries == {
        mock_config_entry.entry_id: {subentry.subentry_id}
    }