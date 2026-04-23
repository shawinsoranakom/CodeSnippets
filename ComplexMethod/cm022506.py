async def test_name(hass: HomeAssistant) -> None:
    """Test event name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.EVENT]
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

    # Unnamed event without device class -> no name
    entity1 = EventEntity()
    entity1._attr_event_types = ["ding"]
    entity1.entity_id = "event.test1"

    # Unnamed event with device class but has_entity_name False -> no name
    entity2 = EventEntity()
    entity2._attr_event_types = ["ding"]
    entity2.entity_id = "event.test2"
    entity2._attr_device_class = EventDeviceClass.DOORBELL

    # Unnamed event with device class and has_entity_name True -> named
    entity3 = EventEntity()
    entity3._attr_event_types = ["ding"]
    entity3.entity_id = "event.test3"
    entity3._attr_device_class = EventDeviceClass.DOORBELL
    entity3._attr_has_entity_name = True

    # Unnamed event with device class and has_entity_name True -> named
    entity4 = EventEntity()
    entity4._attr_event_types = ["ding"]
    entity4.entity_id = "event.test4"
    entity4.entity_description = EventEntityDescription(
        "test",
        EventDeviceClass.DOORBELL,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test event platform via config entry."""
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
    assert state.attributes == {"event_types": ["ding"], "event_type": None}

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes == {
        "event_types": ["ding"],
        "event_type": None,
        "device_class": "doorbell",
    }

    state = hass.states.get(entity3.entity_id)
    assert state
    assert state.attributes == {
        "event_types": ["ding"],
        "event_type": None,
        "device_class": "doorbell",
        "friendly_name": "Doorbell",
    }

    state = hass.states.get(entity4.entity_id)
    assert state
    assert state.attributes == {
        "event_types": ["ding"],
        "event_type": None,
        "device_class": "doorbell",
        "friendly_name": "Doorbell",
    }