async def test_name(hass: HomeAssistant) -> None:
    """Test update name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.UPDATE]
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
        ),
    )

    # Unnamed update entity without device class -> no name
    entity1 = UpdateEntity()
    entity1.entity_id = "update.test1"

    # Unnamed update entity with device class but has_entity_name False -> no name
    entity2 = UpdateEntity()
    entity2.entity_id = "update.test2"
    entity2._attr_device_class = UpdateDeviceClass.FIRMWARE

    # Unnamed update entity with device class and has_entity_name True -> named
    entity3 = UpdateEntity()
    entity3.entity_id = "update.test3"
    entity3._attr_device_class = UpdateDeviceClass.FIRMWARE
    entity3._attr_has_entity_name = True

    # Unnamed update entity with device class and has_entity_name True -> named
    entity4 = UpdateEntity()
    entity4.entity_id = "update.test4"
    entity4.entity_description = UpdateEntityDescription(
        "test",
        UpdateDeviceClass.FIRMWARE,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test update platform via config entry."""
        async_add_entities([entity1, entity2, entity3, entity4])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity1.entity_id)
    assert state
    assert "device_class" not in state.attributes
    assert "friendly_name" not in state.attributes

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes.get("device_class") == "firmware"
    assert "friendly_name" not in state.attributes

    expected = {
        "device_class": "firmware",
        "friendly_name": "Firmware",
    }
    state = hass.states.get(entity3.entity_id)
    assert state
    assert expected.items() <= state.attributes.items()

    state = hass.states.get(entity4.entity_id)
    assert state
    assert expected.items() <= state.attributes.items()