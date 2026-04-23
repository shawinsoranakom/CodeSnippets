async def test_change_device_source(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test remove the device registry configuration entry when the source entity changes."""
    # Configure source entity 1 (with a linked device)
    source_config_entry_1 = MockConfigEntry()
    source_config_entry_1.add_to_hass(hass)
    source_device_entry_1 = device_registry.async_get_or_create(
        config_entry_id=source_config_entry_1.entry_id,
        identifiers={("sensor", "identifier_test1")},
        connections={("mac", "20:31:32:33:34:35")},
    )
    source_entity_1 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source1",
        config_entry=source_config_entry_1,
        device_id=source_device_entry_1.id,
    )

    # Configure source entity 2 (with a linked device)
    source_config_entry_2 = MockConfigEntry()
    source_config_entry_2.add_to_hass(hass)
    source_device_entry_2 = device_registry.async_get_or_create(
        config_entry_id=source_config_entry_2.entry_id,
        identifiers={("sensor", "identifier_test2")},
        connections={("mac", "30:31:32:33:34:35")},
    )
    source_entity_2 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source2",
        config_entry=source_config_entry_2,
        device_id=source_device_entry_2.id,
    )

    # Configure source entity 3 (without a device)
    source_config_entry_3 = MockConfigEntry()
    source_config_entry_3.add_to_hass(hass)
    source_entity_3 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source3",
        config_entry=source_config_entry_3,
    )

    await hass.async_block_till_done()

    input_sensor_entity_id_1 = "sensor.test_source1"
    input_sensor_entity_id_2 = "sensor.test_source2"
    input_sensor_entity_id_3 = "sensor.test_source3"

    # Test the existence of configured source entities
    assert entity_registry.async_get(input_sensor_entity_id_1) is not None
    assert entity_registry.async_get(input_sensor_entity_id_2) is not None
    assert entity_registry.async_get(input_sensor_entity_id_3) is not None

    # Setup the config entry with source entity 1 (with a linked device)
    current_entity_source = source_entity_1
    utility_meter_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Energy",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
            "tariffs": [],
        },
        title="Energy",
    )
    utility_meter_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    await hass.async_block_till_done()

    # Confirm that the configuration entry has not been added to the source entity 1 (current) device registry
    current_device = device_registry.async_get(
        device_id=current_entity_source.device_id
    )
    assert utility_meter_config_entry.entry_id not in current_device.config_entries

    # Check that the entities are linked to the expected device
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        assert utility_meter_entity.device_id == source_entity_1.device_id

    # Change configuration options to use source entity 2 (with a linked device) and reload the integration
    previous_entity_source = source_entity_1
    current_entity_source = source_entity_2

    result = await hass.config_entries.options.async_init(
        utility_meter_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # Confirm that the configuration entry is not in the source entity 1 (previous) device registry
    previous_device = device_registry.async_get(
        device_id=previous_entity_source.device_id
    )
    assert utility_meter_config_entry.entry_id not in previous_device.config_entries

    # Confirm that the configuration entry is not in to the source entity 2 (current) device registry
    current_device = device_registry.async_get(
        device_id=current_entity_source.device_id
    )
    assert utility_meter_config_entry.entry_id not in current_device.config_entries

    # Check that the entities are linked to the expected device
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        assert utility_meter_entity.device_id == source_entity_2.device_id

    # Change configuration options to use source entity 3 (without a device) and reload the integration
    previous_entity_source = source_entity_2
    current_entity_source = source_entity_3

    result = await hass.config_entries.options.async_init(
        utility_meter_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # Confirm that the configuration entry has is not in the source entity 2 (previous) device registry
    previous_device = device_registry.async_get(
        device_id=previous_entity_source.device_id
    )
    assert utility_meter_config_entry.entry_id not in previous_device.config_entries

    # Check that the entities are no longer linked to a device
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        assert utility_meter_entity.device_id is None

    # Confirm that there is no device with the helper configuration entry
    assert (
        dr.async_entries_for_config_entry(
            device_registry, utility_meter_config_entry.entry_id
        )
        == []
    )

    # Change configuration options to use source entity 2 (with a linked device) and reload the integration
    previous_entity_source = source_entity_3
    current_entity_source = source_entity_2

    result = await hass.config_entries.options.async_init(
        utility_meter_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # Confirm that the configuration entry is not in the source entity 2 (current) device registry
    current_device = device_registry.async_get(
        device_id=current_entity_source.device_id
    )
    assert utility_meter_config_entry.entry_id not in current_device.config_entries

    # Check that the entities are linked to the expected device
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        assert utility_meter_entity.device_id == source_entity_2.device_id