async def test_filter_on_load(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test we transform some data when loading from storage."""
    hass_storage[er.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "data": {
            "entities": [
                {
                    "entity_id": "test.named",
                    "platform": "super_platform",
                    "unique_id": "with-name",
                    "name": "registry override",
                },
                # This entity's name should be None
                {
                    "entity_id": "test.no_name",
                    "platform": "super_platform",
                    "unique_id": "without-name",
                },
                {
                    "entity_id": "test.disabled_user",
                    "platform": "super_platform",
                    "unique_id": "disabled-user",
                    "disabled_by": "user",  # We store the string representation
                },
                {
                    "entity_id": "test.disabled_hass",
                    "platform": "super_platform",
                    "unique_id": "disabled-hass",
                    "disabled_by": "hass",  # We store the string representation
                },
            ]
        },
    }

    await er.async_load(hass)
    registry = er.async_get(hass)

    assert len(registry.entities) == 4
    assert set(registry.entities.keys()) == {
        "test.disabled_hass",
        "test.disabled_user",
        "test.named",
        "test.no_name",
    }

    entry_with_name = registry.async_get_or_create(
        "test", "super_platform", "with-name"
    )
    entry_without_name = registry.async_get_or_create(
        "test", "super_platform", "without-name"
    )
    assert entry_with_name.name == "registry override"
    assert entry_without_name.name is None
    assert not entry_with_name.disabled
    assert entry_with_name.created_at == utc_from_timestamp(0)
    assert entry_with_name.modified_at == utc_from_timestamp(0)

    entry_disabled_hass = registry.async_get_or_create(
        "test", "super_platform", "disabled-hass"
    )
    entry_disabled_user = registry.async_get_or_create(
        "test", "super_platform", "disabled-user"
    )
    assert entry_disabled_hass.disabled
    assert entry_disabled_hass.disabled_by is er.RegistryEntryDisabler.HASS
    assert entry_disabled_user.disabled
    assert entry_disabled_user.disabled_by is er.RegistryEntryDisabler.USER