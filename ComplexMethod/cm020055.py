async def test_local_setup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    two_zone_local,
    setup_risco_local,
) -> None:
    """Test entity setup."""
    assert entity_registry.async_is_registered(FIRST_ENTITY_ID)
    assert entity_registry.async_is_registered(SECOND_ENTITY_ID)
    assert entity_registry.async_is_registered(FIRST_ALARMED_ENTITY_ID)
    assert entity_registry.async_is_registered(SECOND_ALARMED_ENTITY_ID)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, TEST_SITE_UUID + "_zone_0_local")}
    )
    assert device is not None
    assert device.manufacturer == "Risco"

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, TEST_SITE_UUID + "_zone_1_local")}
    )
    assert device is not None
    assert device.manufacturer == "Risco"

    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_SITE_UUID)})
    assert device is not None
    assert device.manufacturer == "Risco"