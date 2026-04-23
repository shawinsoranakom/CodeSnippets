async def test_entity_id_to_device_device_id(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test returning an entity's device / device ID."""
    config_entry = MockConfigEntry(domain="my")
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        identifiers={("test", "current_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=config_entry.entry_id,
    )
    assert device is not None

    # Entity registry
    entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        config_entry=config_entry,
        device_id=device.id,
    )
    await hass.async_block_till_done()
    assert entity_registry.async_get("sensor.test_source") is not None

    device_id = async_entity_id_to_device_id(
        hass,
        entity_id_or_uuid=entity.entity_id,
    )
    assert device_id == device.id
    assert (
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid=entity.entity_id,
        )
        == device
    )

    assert (
        async_entity_id_to_device_id(
            hass,
            entity_id_or_uuid="unknown.entity_id",
        )
        is None
    )
    assert (
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid="unknown.entity_id",
        )
        is None
    )

    device_id = async_entity_id_to_device_id(
        hass,
        entity_id_or_uuid=entity.id,
    )
    assert device_id == device.id
    assert (
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid=entity.id,
        )
        == device
    )

    with pytest.raises(vol.Invalid):
        async_entity_id_to_device_id(
            hass,
            entity_id_or_uuid="unknown_uuid",
        )

    with pytest.raises(vol.Invalid):
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid="unknown_uuid",
        )