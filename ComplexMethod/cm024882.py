async def test_update_capabilities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entity capabilities are updated automatically."""
    platform = MockEntityPlatform(hass)

    ent = MockEntity(unique_id="qwer")
    await platform.async_add_entities([ent])

    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities is None
    assert entry.device_class is None
    assert entry.supported_features == 0

    ent._values["capability_attributes"] = {"bla": "blu"}
    ent._values["device_class"] = "some_class"
    ent._values["supported_features"] = 127
    ent.async_write_ha_state()
    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities == {"bla": "blu"}
    assert entry.original_device_class == "some_class"
    assert entry.supported_features == 127

    ent._values["capability_attributes"] = None
    ent._values["device_class"] = None
    ent._values["supported_features"] = None
    ent.async_write_ha_state()
    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities is None
    assert entry.original_device_class is None
    assert entry.supported_features == 0

    # Device class can be overridden by user, make sure that does not break the
    # automatic updating.
    entity_registry.async_update_entity(ent.entity_id, device_class="set_by_user")
    await hass.async_block_till_done()
    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities is None
    assert entry.original_device_class is None
    assert entry.supported_features == 0

    # This will not trigger a state change because the device class is shadowed
    # by the entity registry
    ent._values["device_class"] = "some_class"
    ent.async_write_ha_state()
    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities is None
    assert entry.original_device_class == "some_class"
    assert entry.supported_features == 0