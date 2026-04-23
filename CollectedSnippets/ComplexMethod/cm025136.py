async def test_labels(
    hass: HomeAssistant,
    label_registry: lr.LabelRegistry,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test labels function."""

    # Test no labels
    info = render_to_info(hass, "{{ labels() }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test one label
    label1 = label_registry.async_create("label1")
    info = render_to_info(hass, "{{ labels() }}")
    assert_result_info(info, [label1.label_id])
    assert info.rate_limit is None

    # Test multiple label
    label2 = label_registry.async_create("label2")
    info = render_to_info(hass, "{{ labels() }}")
    assert_result_info(info, [label1.label_id, label2.label_id])
    assert info.rate_limit is None

    # Test non-existing entity ID
    info = render_to_info(hass, "{{ labels('sensor.fake') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 'sensor.fake' | labels }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test non existing device ID (hex value)
    info = render_to_info(hass, "{{ labels('123abc') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ '123abc' | labels }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Create a device & entity for testing
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )

    # Test entity, which has no labels
    info = render_to_info(hass, f"{{{{ labels('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{entity_entry.entity_id}' | labels }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test device, which has no labels
    info = render_to_info(hass, f"{{{{ labels('{device_entry.id}') }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{device_entry.id}' | labels }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Add labels to the entity & device
    device_entry = device_registry.async_update_device(
        device_entry.id, labels=[label1.label_id]
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, labels=[label2.label_id]
    )

    # Test entity, which now has a label
    info = render_to_info(hass, f"{{{{ '{entity_entry.entity_id}' | labels }}}}")
    assert_result_info(info, [label2.label_id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ labels('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, [label2.label_id])
    assert info.rate_limit is None

    # Test device, which now has a label
    info = render_to_info(hass, f"{{{{ '{device_entry.id}' | labels }}}}")
    assert_result_info(info, [label1.label_id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ labels('{device_entry.id}') }}}}")
    assert_result_info(info, [label1.label_id])
    assert info.rate_limit is None

    # Create area for testing
    area = area_registry.async_create("living room")

    # Test area, which has no labels
    info = render_to_info(hass, f"{{{{ '{area.id}' | labels }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ labels('{area.id}') }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Add label to the area
    area_registry.async_update(area.id, labels=[label1.label_id, label2.label_id])

    # Test area, which now has labels
    info = render_to_info(hass, f"{{{{ '{area.id}' | labels }}}}")
    assert_result_info(info, [label1.label_id, label2.label_id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ labels('{area.id}') }}}}")
    assert_result_info(info, [label1.label_id, label2.label_id])
    assert info.rate_limit is None