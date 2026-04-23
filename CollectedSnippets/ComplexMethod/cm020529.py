async def test_migration_v3_to_v5(
    hass: HomeAssistant,
    mock_portainer_client: AsyncMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from v3 config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://test_host",
            CONF_API_TOKEN: "test_key",
            CONF_VERIFY_SSL: True,
        },
        unique_id="1",
        version=3,
    )
    entry.add_to_hass(hass)
    assert entry.version == 3

    endpoint_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.entry_id}_endpoint_1")},
        name="Test Endpoint",
    )

    original_container_identifier = f"{entry.entry_id}_adguard"
    container_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, original_container_identifier)},
        via_device=(DOMAIN, f"{entry.entry_id}_endpoint_1"),
        name="Test Container",
    )

    container_entity = entity_registry.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id=f"{entry.entry_id}_adguard_container",
        config_entry=entry,
        device_id=container_device.id,
        original_name="Test Container Switch",
    )

    assert container_device.via_device_id == endpoint_device.id
    assert container_device.identifiers == {(DOMAIN, original_container_identifier)}
    assert container_entity.unique_id == f"{entry.entry_id}_adguard_container"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 5

    # Fetch again, to assert the new identifiers
    container_after = device_registry.async_get(container_device.id)
    entity_after = entity_registry.async_get(container_entity.entity_id)

    assert container_after.identifiers == {
        (DOMAIN, original_container_identifier),
        (DOMAIN, f"{entry.entry_id}_1_adguard"),
    }
    assert entity_after.unique_id == f"{entry.entry_id}_1_adguard_container"