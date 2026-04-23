async def test_migration_from_v1_disabled(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    config_entry_disabled_by: list[ConfigEntryDisabler | None],
    merged_config_entry_disabled_by: ConfigEntryDisabler | None,
    sensor_subentry_data: list[dict[str, Any]],
    main_config_entry: int,
) -> None:
    """Test migration where the config entries are disabled."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "1234", CONF_STATION_NUMBER: 4584},
        version=1,
        unique_id="4584",
        title="de Jongweg, Utrecht",
        disabled_by=config_entry_disabled_by[0],
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "1234", CONF_STATION_NUMBER: 4585},
        version=1,
        unique_id="4585",
        title="Not de Jongweg, Utrecht",
        disabled_by=config_entry_disabled_by[1],
    )
    mock_config_entry_2.add_to_hass(hass)
    mock_config_entries = [mock_config_entry, mock_config_entry_2]

    device_1 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, mock_config_entry.unique_id)},
        name=mock_config_entry.title,
        entry_type=dr.DeviceEntryType.SERVICE,
        disabled_by=DeviceEntryDisabler.CONFIG_ENTRY,
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        mock_config_entry.unique_id,
        config_entry=mock_config_entry,
        device_id=device_1.id,
        suggested_object_id="de_jongweg_utrecht_air_quality_index",
        disabled_by=RegistryEntryDisabler.CONFIG_ENTRY,
    )

    device_2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_2.entry_id,
        identifiers={(DOMAIN, mock_config_entry_2.unique_id)},
        name=mock_config_entry_2.title,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        mock_config_entry_2.unique_id,
        config_entry=mock_config_entry_2,
        device_id=device_2.id,
        suggested_object_id="not_de_jongweg_utrecht_air_quality_index",
    )

    devices = [device_1, device_2]

    # Run migration
    with patch(
        "homeassistant.components.waqi.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.disabled_by is merged_config_entry_disabled_by
    assert entry.version == 2
    assert entry.minor_version == 1
    assert not entry.options
    assert entry.title == "WAQI"
    assert len(entry.subentries) == 2
    station_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "station"
    ]
    assert len(station_subentries) == 2
    for subentry in station_subentries:
        assert subentry.data == {CONF_STATION_NUMBER: int(subentry.unique_id)}
        assert "de Jongweg" in subentry.title

    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry_2.entry_id)}
    )

    for idx, subentry in enumerate(station_subentries):
        subentry_data = sensor_subentry_data[idx]
        entity = entity_registry.async_get(subentry_data["sensor_entity_id"])
        assert entity.unique_id == subentry.unique_id
        assert entity.config_subentry_id == subentry.subentry_id
        assert entity.config_entry_id == entry.entry_id
        assert entity.disabled_by is subentry_data["entity_disabled_by"]

        assert (
            device := device_registry.async_get_device(
                identifiers={(DOMAIN, subentry.unique_id)}
            )
        )
        assert device.identifiers == {(DOMAIN, subentry.unique_id)}
        assert device.id == devices[subentry_data["device"]].id
        assert device.config_entries == {
            mock_config_entries[main_config_entry].entry_id
        }
        assert device.config_entries_subentries == {
            mock_config_entries[main_config_entry].entry_id: {subentry.subentry_id}
        }
        assert device.disabled_by is subentry_data["device_disabled_by"]