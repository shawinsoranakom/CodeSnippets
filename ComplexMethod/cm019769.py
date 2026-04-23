async def test_name(hass: HomeAssistant, config_flow_fixture: None) -> None:
    """Test notify name."""

    mock_platform(hass, "test.config_flow")
    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
        ),
    )

    # Unnamed notify entity -> no name
    entity1 = NotifyEntity()
    entity1.entity_id = "notify.test1"

    # Unnamed notify entity and has_entity_name True -> unnamed
    entity2 = NotifyEntity()
    entity2.entity_id = "notify.test3"
    entity2._attr_has_entity_name = True

    # Named notify entity and has_entity_name True -> named
    entity3 = NotifyEntity()
    entity3.entity_id = "notify.test4"
    entity3.entity_description = NotifyEntityDescription("test", has_entity_name=True)

    setup_test_component_platform(
        hass, DOMAIN, [entity1, entity2, entity3], from_config_entry=True
    )

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity1.entity_id)
    assert state
    assert state.attributes == {"supported_features": NotifyEntityFeature(0)}

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes == {"supported_features": NotifyEntityFeature(0)}

    state = hass.states.get(entity3.entity_id)
    assert state
    assert state.attributes == {"supported_features": NotifyEntityFeature(0)}