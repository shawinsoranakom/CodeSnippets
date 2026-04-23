async def test_migrate_to_new_unique_id(
    hass: HomeAssistant,
    fc_class_mock,
    fh_class_mock,
    fs_class_mock,
    entity_registry: EntityRegistry,
    device_registry: dr.DeviceRegistry,
    ssid_1: str,
    ssid_2: str,
    old_descriptions: list[str],
    new_identifiers: list[str],
) -> None:
    """Test migrate from old unique ids to new unique ids."""

    MOCK_UNIQUE_ID = "1234567890"

    fc_class_mock.return_value.override_services(
        wifi_services_with_ssids(ssid_1, ssid_2)
    )

    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_USER_DATA, unique_id=MOCK_UNIQUE_ID
    )
    entry.add_to_hass(hass)

    entity_ids: list[str] = []
    old_unique_ids: list[str] = []
    new_unique_ids: list[str] = []
    for old_description, new_identifier in zip(
        old_descriptions, new_identifiers, strict=True
    ):
        old_unique_id = f"{MOCK_SERIAL_NUMBER}-{slugify(old_description)}"
        new_unique_id = f"{MOCK_SERIAL_NUMBER}-wi_fi_{new_identifier}"
        old_unique_ids.append(old_unique_id)
        new_unique_ids.append(new_unique_id)
        entity_ids.append(f"switch.fritz_{slugify(old_unique_id)}")

        entity_registry.async_get_or_create(
            disabled_by=None,
            domain=SWITCH_DOMAIN,
            platform=DOMAIN,
            unique_id=old_unique_id,
            config_entry=entry,
        )

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)},
        connections={
            (dr.CONNECTION_NETWORK_MAC, MOCK_MESH_MASTER_MAC),
        },
    )
    await hass.async_block_till_done()

    for entity_id, old_unique_id in zip(entity_ids, old_unique_ids, strict=True):
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.unique_id == old_unique_id

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for entity_id, new_unique_id in zip(entity_ids, new_unique_ids, strict=True):
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.unique_id == new_unique_id