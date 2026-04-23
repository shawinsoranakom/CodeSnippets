async def test_area_id(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test area_id function."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    # Test non existing entity id
    info = render_to_info(hass, "{{ area_id('sensor.fake') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existing device id (hex value)
    info = render_to_info(hass, "{{ area_id('123abc') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existing area name
    info = render_to_info(hass, "{{ area_id('fake area name') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ area_id(56) }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    area_registry.async_get_or_create("sensor.fake")

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
    info = render_to_info(hass, f"{{{{ area_id('{device_entry.id}') }}}}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_id('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test device ID, entity ID and area name as input with area name that looks like
    # a device ID. Try a filter too
    area_entry_hex = area_registry.async_get_or_create("123abc")
    device_entry = device_registry.async_update_device(
        device_entry.id, area_id=area_entry_hex.id
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=area_entry_hex.id
    )

    info = render_to_info(hass, f"{{{{ '{device_entry.id}' | area_id }}}}")
    assert_result_info(info, area_entry_hex.id)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_id('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, area_entry_hex.id)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_id('{area_entry_hex.name}') }}}}")
    assert_result_info(info, area_entry_hex.id)
    assert info.rate_limit is None

    # Test device ID, entity ID and area name as input with area name that looks like an
    # entity ID
    area_entry_entity_id = area_registry.async_get_or_create("sensor.fake")
    device_entry = device_registry.async_update_device(
        device_entry.id, area_id=area_entry_entity_id.id
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=area_entry_entity_id.id
    )

    info = render_to_info(hass, f"{{{{ area_id('{device_entry.id}') }}}}")
    assert_result_info(info, area_entry_entity_id.id)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_id('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, area_entry_entity_id.id)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ area_id('{area_entry_entity_id.name}') }}}}")
    assert_result_info(info, area_entry_entity_id.id)
    assert info.rate_limit is None

    # Make sure that when entity doesn't have an area but its device does, that's what
    # gets returned
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=area_entry_entity_id.id
    )

    info = render_to_info(hass, f"{{{{ area_id('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, area_entry_entity_id.id)
    assert info.rate_limit is None