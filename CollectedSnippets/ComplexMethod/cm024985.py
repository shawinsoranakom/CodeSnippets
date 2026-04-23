async def test_device_info_called(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test device info is forwarded correctly."""
    config_entry = MockConfigEntry(
        entry_id="super-mock-id",
        subentries_data=(
            ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ),
    )
    config_entry.add_to_hass(hass)
    via = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections=set(),
        identifiers={("hue", "via-id")},
        manufacturer="manufacturer",
        model="via",
    )

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setup entry method."""
        async_add_entities(
            [
                # Invalid device info
                MockEntity(unique_id="abcd", device_info={}),
                # Valid device info
                MockEntity(
                    unique_id="qwer",
                    device_info={
                        "identifiers": {("hue", "1234")},
                        "configuration_url": "http://192.168.0.100/config",
                        "connections": {(dr.CONNECTION_NETWORK_MAC, "abcd")},
                        "manufacturer": "test-manuf",
                        "model": "test-model",
                        "name": "test-name",
                        "sw_version": "test-sw",
                        "hw_version": "test-hw",
                        "suggested_area": "Heliport",
                        "entry_type": dr.DeviceEntryType.SERVICE,
                        "via_device": ("hue", "via-id"),
                    },
                ),
            ]
        )
        async_add_entities(
            [
                # Valid device info
                MockEntity(
                    unique_id="efgh",
                    device_info={
                        "identifiers": {("hue", "efgh")},
                        "configuration_url": "http://192.168.0.100/config",
                        "connections": {(dr.CONNECTION_NETWORK_MAC, "efgh")},
                        "manufacturer": "test-manuf",
                        "model": "test-model",
                        "name": "test-name",
                        "sw_version": "test-sw",
                        "hw_version": "test-hw",
                        "suggested_area": "Heliport",
                        "entry_type": dr.DeviceEntryType.SERVICE,
                        "via_device": ("hue", "via-id"),
                    },
                ),
            ],
            config_subentry_id="mock-subentry-id-1",
        )

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    entity_platform = MockEntityPlatform(
        hass, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) == 3

    device = device_registry.async_get_device(identifiers={("hue", "1234")})
    assert device == snapshot
    assert device.config_entries == {config_entry.entry_id}
    assert device.config_entries_subentries == {config_entry.entry_id: {None}}
    assert device.primary_config_entry == config_entry.entry_id
    assert device.via_device_id == via.id
    device = device_registry.async_get_device(identifiers={("hue", "efgh")})
    assert device == snapshot
    assert device.config_entries == {config_entry.entry_id}
    assert device.config_entries_subentries == {
        config_entry.entry_id: {"mock-subentry-id-1"}
    }
    assert device.primary_config_entry == config_entry.entry_id
    assert device.via_device_id == via.id