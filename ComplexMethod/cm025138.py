async def test_label_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    label_registry: lr.LabelRegistry,
) -> None:
    """Test label_devices function."""

    # Test non existing device ID
    info = render_to_info(hass, "{{ label_devices('deadbeef') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 'deadbeef' | label_devices }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ label_devices(42) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 42 | label_devices }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Create a fake config entry with a device
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    # Add a label to it
    label = label_registry.async_create("Romantic Lights")
    device_registry.async_update_device(device_entry.id, labels=[label.label_id])

    # Get the devices from a label by its ID
    info = render_to_info(hass, f"{{{{ label_devices('{label.label_id}') }}}}")
    assert_result_info(info, [device_entry.id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{label.label_id}' | label_devices }}}}")
    assert_result_info(info, [device_entry.id])
    assert info.rate_limit is None

    # Get the devices from a label by its name
    info = render_to_info(hass, f"{{{{ label_devices('{label.name}') }}}}")
    assert_result_info(info, [device_entry.id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{label.name}' | label_devices }}}}")
    assert_result_info(info, [device_entry.id])
    assert info.rate_limit is None