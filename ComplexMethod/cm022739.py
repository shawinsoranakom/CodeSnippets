async def test_aid_generation(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test generating aids."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    light_ent = entity_registry.async_get_or_create(
        "light", "device", "unique_id", device_id=device_entry.id
    )
    light_ent2 = entity_registry.async_get_or_create(
        "light", "device", "other_unique_id", device_id=device_entry.id
    )
    remote_ent = entity_registry.async_get_or_create(
        "remote", "device", "unique_id", device_id=device_entry.id
    )
    hass.states.async_set(light_ent.entity_id, "on")
    hass.states.async_set(light_ent2.entity_id, "on")
    hass.states.async_set(remote_ent.entity_id, "on")
    hass.states.async_set("remote.has_no_unique_id", "on")

    with patch(
        "homeassistant.components.homekit.aidmanager.AccessoryAidStorage.async_schedule_save"
    ):
        aid_storage = AccessoryAidStorage(hass, config_entry)
    await aid_storage.async_initialize()

    for _ in range(2):
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id(light_ent.entity_id)
            == 1953095294
        )
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id(light_ent2.entity_id)
            == 1975378727
        )
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id(remote_ent.entity_id)
            == 3508011530
        )
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id("remote.has_no_unique_id")
            == 1751603975
        )

    aid_storage.delete_aid(get_system_unique_id(light_ent, light_ent.unique_id))
    aid_storage.delete_aid(get_system_unique_id(light_ent2, light_ent2.unique_id))
    aid_storage.delete_aid(get_system_unique_id(remote_ent, remote_ent.unique_id))
    aid_storage.delete_aid("non-existent-one")

    for _ in range(2):
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id(light_ent.entity_id)
            == 1953095294
        )
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id(light_ent2.entity_id)
            == 1975378727
        )
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id(remote_ent.entity_id)
            == 3508011530
        )
        assert (
            aid_storage.get_or_allocate_aid_for_entity_id("remote.has_no_unique_id")
            == 1751603975
        )