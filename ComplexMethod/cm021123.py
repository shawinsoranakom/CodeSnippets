async def test_switch_setup_light(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    light: Light,
) -> None:
    """Test switch entity setup for light devices."""

    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.SWITCH, 4, 3)

    description = LIGHT_SWITCHES[1]

    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, light, description
    )

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION

    description = LIGHT_SWITCHES[0]

    unique_id = f"{light.mac}_{description.key}"
    entity_id = f"switch.test_light_{description.translation_key}"

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.disabled is True
    assert entity.unique_id == unique_id

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION