async def test_name(hass: HomeAssistant) -> None:
    """Test button name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.BUTTON]
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

    # Unnamed button without device class -> no name
    entity1 = ButtonEntity()
    entity1.entity_id = "button.test1"

    # Unnamed button with device class but has_entity_name False -> no name
    entity2 = ButtonEntity()
    entity2.entity_id = "button.test2"
    entity2._attr_device_class = ButtonDeviceClass.RESTART

    # Unnamed button with device class and has_entity_name True -> named
    entity3 = ButtonEntity()
    entity3.entity_id = "button.test3"
    entity3._attr_device_class = ButtonDeviceClass.RESTART
    entity3._attr_has_entity_name = True

    # Unnamed button with device class and has_entity_name True -> named
    entity4 = ButtonEntity()
    entity4.entity_id = "sensor.test4"
    entity4.entity_description = ButtonEntityDescription(
        "test",
        ButtonDeviceClass.RESTART,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test button platform via config entry."""
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
    assert state.attributes == {}

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes == {"device_class": "restart"}

    state = hass.states.get(entity3.entity_id)
    assert state
    assert state.attributes == {"device_class": "restart", "friendly_name": "Restart"}

    state = hass.states.get(entity4.entity_id)
    assert state
    assert state.attributes == {"device_class": "restart", "friendly_name": "Restart"}