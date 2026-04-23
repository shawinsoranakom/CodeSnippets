async def test_migration_with_all_unique_ids(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test if migration works when we have all unique ids."""
    entry = create_entry(hass, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)
    device = create_device(entry, device_registry, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)

    assert entry is not None
    assert device is not None

    v1 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=VOC_V1.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    v2 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=VOC_V2.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    v3 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=VOC_V3.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 0

    inject_bluetooth_service_info(
        hass,
        WAVE_SERVICE_INFO,
    )

    await hass.async_block_till_done()

    with patch_airthings_device_update():
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert len(hass.states.async_all()) > 0

    # No migration should happen, unique id should be the same as before
    assert entity_registry.async_get(v1.entity_id).unique_id == VOC_V1.unique_id
    assert entity_registry.async_get(v2.entity_id).unique_id == VOC_V2.unique_id
    assert entity_registry.async_get(v3.entity_id).unique_id == VOC_V3.unique_id