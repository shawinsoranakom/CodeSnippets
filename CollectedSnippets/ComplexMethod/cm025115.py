async def test_device_name(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test device_name function."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    # Test non existing entity id
    info = render_to_info(hass, "{{ device_name('sensor.fake') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existing device id
    info = render_to_info(hass, "{{ device_name('1234567890') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ device_name(56) }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test device with single entity
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        name="A light",
    )
    entity_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    info = render_to_info(hass, f"{{{{ device_name('{device_entry.id}') }}}}")
    assert_result_info(info, device_entry.name)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ device_name('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, device_entry.name)
    assert info.rate_limit is None

    # Test device after renaming
    device_entry = device_registry.async_update_device(
        device_entry.id,
        name_by_user="My light",
    )

    info = render_to_info(hass, f"{{{{ device_name('{device_entry.id}') }}}}")
    assert_result_info(info, device_entry.name_by_user)
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ device_name('{entity_entry.entity_id}') }}}}")
    assert_result_info(info, device_entry.name_by_user)
    assert info.rate_limit is None