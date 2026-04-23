async def test_floor_entities(
    hass: HomeAssistant,
    floor_registry: fr.FloorRegistry,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test floor_entities function."""

    # Test non existing floor ID
    info = render_to_info(hass, "{{ floor_entities('skyring') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 'skyring' | floor_entities }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ floor_entities(42) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 42 | floor_entities }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    floor = floor_registry.async_create("First floor")
    area1 = area_registry.async_create("Living room")
    area2 = area_registry.async_create("Dining room")
    area_registry.async_update(area1.id, floor_id=floor.floor_id)
    area_registry.async_update(area2.id, floor_id=floor.floor_id)

    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)
    entity_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "living_room",
        config_entry=config_entry,
    )
    entity_registry.async_update_entity(entity_entry.entity_id, area_id=area1.id)
    entity_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "dining_room",
        config_entry=config_entry,
    )
    entity_registry.async_update_entity(entity_entry.entity_id, area_id=area2.id)

    # Get entities by floor ID
    expected = ["light.hue_living_room", "light.hue_dining_room"]
    info = render_to_info(hass, f"{{{{ floor_entities('{floor.floor_id}') }}}}")
    assert_result_info(info, expected)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{floor.floor_id}' | floor_entities }}}}")
    assert_result_info(info, expected)
    assert info.rate_limit is None

    # Get entities by floor name
    info = render_to_info(hass, f"{{{{ floor_entities('{floor.name}') }}}}")
    assert_result_info(info, expected)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{floor.name}' | floor_entities }}}}")
    assert_result_info(info, expected)
    assert info.rate_limit is None