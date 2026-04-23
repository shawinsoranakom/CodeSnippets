async def test_device_info_not_overrides(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test device info is forwarded correctly."""
    config_entry = MockConfigEntry(entry_id="super-mock-id")
    config_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "abcd")},
        manufacturer="test-manufacturer",
        model="test-model",
    )

    assert device.manufacturer == "test-manufacturer"
    assert device.model == "test-model"

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setup entry method."""
        async_add_entities(
            [
                MockEntity(
                    unique_id="qwer",
                    device_info={
                        "connections": {(dr.CONNECTION_NETWORK_MAC, "abcd")},
                        "default_name": "default name 1",
                        "default_model": "default model 1",
                        "default_manufacturer": "default manufacturer 1",
                    },
                )
            ]
        )

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    entity_platform = MockEntityPlatform(
        hass, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await hass.async_block_till_done()

    device2 = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, "abcd")}
    )
    assert device2 is not None
    assert device.id == device2.id
    assert device2.manufacturer == "test-manufacturer"
    assert device2.model == "test-model"