async def test_label_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    label_registry: lr.LabelRegistry,
) -> None:
    """Test label_entities function."""

    # Test non existing device ID
    info = render_to_info(hass, "{{ label_entities('deadbeef') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 'deadbeef' | label_entities }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ label_entities(42) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 42 | label_entities }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Create a fake config entry with a entity
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)
    entity_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
    )

    # Add a label to the entity
    label = label_registry.async_create("Romantic Lights")
    entity_registry.async_update_entity(entity_entry.entity_id, labels={label.label_id})

    # Get entities by label ID
    info = render_to_info(hass, f"{{{{ label_entities('{label.label_id}') }}}}")
    assert_result_info(info, ["light.hue_5678"])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{label.label_id}' | label_entities }}}}")
    assert_result_info(info, ["light.hue_5678"])
    assert info.rate_limit is None

    # Get entities by label name
    info = render_to_info(hass, f"{{{{ label_entities('{label.name}') }}}}")
    assert_result_info(info, ["light.hue_5678"])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{label.name}' | label_entities }}}}")
    assert_result_info(info, ["light.hue_5678"])
    assert info.rate_limit is None