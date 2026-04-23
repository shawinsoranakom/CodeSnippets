async def test_name(hass: HomeAssistant) -> None:
    """Test number name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.NUMBER]
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

    # Unnamed number without device class -> no name
    entity1 = NumberEntity()
    entity1.entity_id = "number.test1"

    # Unnamed number with device class but has_entity_name False -> no name
    entity2 = NumberEntity()
    entity2.entity_id = "number.test2"
    entity2._attr_device_class = NumberDeviceClass.TEMPERATURE

    # Unnamed number with device class and has_entity_name True -> named
    entity3 = NumberEntity()
    entity3.entity_id = "number.test3"
    entity3._attr_device_class = NumberDeviceClass.TEMPERATURE
    entity3._attr_has_entity_name = True

    # Unnamed number with device class and has_entity_name True -> named
    entity4 = NumberEntity()
    entity4.entity_id = "number.test4"
    entity4.entity_description = NumberEntityDescription(
        "test",
        NumberDeviceClass.TEMPERATURE,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test number platform via config entry."""
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
    assert state.attributes == {
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes == {
        "device_class": "temperature",
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }

    state = hass.states.get(entity3.entity_id)
    assert state
    assert state.attributes == {
        "device_class": "temperature",
        "friendly_name": "Temperature",
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }

    state = hass.states.get(entity4.entity_id)
    assert state
    assert state.attributes == {
        "device_class": "temperature",
        "friendly_name": "Temperature",
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }