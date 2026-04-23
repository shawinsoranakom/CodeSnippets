async def test_migration_from(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    from_version,
    from_minor_version,
    config_data,
    unique_id,
    mock_cookidoo_client: AsyncMock,
) -> None:
    """Test different expected migration paths."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=config_data,
        title=f"MIGRATION_TEST from {from_version}.{from_minor_version}",
        version=from_version,
        minor_version=from_minor_version,
        unique_id=unique_id,
        entry_id=OLD_ENTRY_ID,
    )
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, OLD_ENTRY_ID)},
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        config_entry=config_entry,
        platform=DOMAIN,
        domain="todo",
        unique_id=f"{OLD_ENTRY_ID}_ingredients",
        device_id=device.id,
    )
    entity_registry.async_get_or_create(
        config_entry=config_entry,
        platform=DOMAIN,
        domain="todo",
        unique_id=f"{OLD_ENTRY_ID}_additional_items",
        device_id=device.id,
    )
    entity_registry.async_get_or_create(
        config_entry=config_entry,
        platform=DOMAIN,
        domain="button",
        unique_id=f"{OLD_ENTRY_ID}_todo_clear",
        device_id=device.id,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state is ConfigEntryState.LOADED

    # Check change in config entry and verify most recent version
    assert config_entry.version == 1
    assert config_entry.minor_version == 2
    assert config_entry.unique_id == TEST_UUID

    assert entity_registry.async_is_registered(
        entity_registry.entities.get_entity_id(
            (
                Platform.TODO,
                DOMAIN,
                f"{TEST_UUID}_ingredients",
            )
        )
    )
    assert entity_registry.async_is_registered(
        entity_registry.entities.get_entity_id(
            (
                Platform.TODO,
                DOMAIN,
                f"{TEST_UUID}_additional_items",
            )
        )
    )
    assert entity_registry.async_is_registered(
        entity_registry.entities.get_entity_id(
            (
                Platform.BUTTON,
                DOMAIN,
                f"{TEST_UUID}_todo_clear",
            )
        )
    )