async def test_area_name(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test area_name function."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    # Test non existing entity id
    info = render_to_info(hass, "{{ area_name('sensor.fake') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existing device id (hex value)
    info = render_to_info(hass, "{{ area_name('123abc') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existing area id
    info = render_to_info(hass, "{{ area_name('1234567890') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ area_name(56) }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test device with single entity, which has no area
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
    info = render_to_info(hass, f"{{{{ area_name('{device_entry.id}') }}}}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_name('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test device ID, entity ID and area id as input. Try a filter too
    area_entry = area_registry.async_get_or_create("123abc")
    device_entry = device_registry.async_update_device(
        device_entry.id, area_id=area_entry.id
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=area_entry.id
    )

    info = render_to_info(hass, f"{{{{ '{device_entry.id}' | area_name }}}}")
    assert_result_info(info, area_entry.name)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_name('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, area_entry.name)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_name('{area_entry.id}') }}}}")
    assert_result_info(info, area_entry.name)
    assert info.rate_limit is None

    # Make sure that when entity doesn't have an area but its device does, that's what
    # gets returned
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=None
    )

    info = render_to_info(hass, f"{{{{ area_name('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, area_entry.name)
    assert info.rate_limit is None