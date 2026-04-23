async def test_update_capabilities_too_often(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entity capabilities are updated automatically."""
    capabilities_too_often_warning = "is updating its capabilities too often"
    platform = MockEntityPlatform(hass)

    ent = MockEntity(unique_id="qwer")
    await platform.async_add_entities([ent])

    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities is None
    assert entry.device_class is None
    assert entry.supported_features == 0

    for supported_features in range(1, entity.CAPABILITIES_UPDATE_LIMIT + 1):
        ent._values["capability_attributes"] = {"bla": "blu"}
        ent._values["device_class"] = "some_class"
        ent._values["supported_features"] = supported_features
        ent.async_write_ha_state()
        entry = entity_registry.async_get(ent.entity_id)
        assert entry.capabilities == {"bla": "blu"}
        assert entry.original_device_class == "some_class"
        assert entry.supported_features == supported_features

    assert capabilities_too_often_warning not in caplog.text

    ent._values["capability_attributes"] = {"bla": "blu"}
    ent._values["device_class"] = "some_class"
    ent._values["supported_features"] = supported_features + 1
    ent.async_write_ha_state()
    entry = entity_registry.async_get(ent.entity_id)
    assert entry.capabilities == {"bla": "blu"}
    assert entry.original_device_class == "some_class"
    assert entry.supported_features == supported_features + 1

    assert capabilities_too_often_warning in caplog.text