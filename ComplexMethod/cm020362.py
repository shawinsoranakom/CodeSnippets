async def test_update_time_segment_invalid_segment_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test validation of segment_id range."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Get the device registry ID
    device_entry = device_registry.async_get_device(identifiers={(DOMAIN, "MIN123456")})
    assert device_entry is not None

    # Test segment_id too low
    with pytest.raises(ServiceValidationError) as excinfo:
        await hass.services.async_call(
            DOMAIN,
            "update_time_segment",
            {
                "device_id": device_entry.id,
                "segment_id": 0,
                "start_time": "09:00",
                "end_time": "11:00",
                "batt_mode": "load_first",
                "enabled": True,
            },
            blocking=True,
        )
    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "invalid_segment_id"
    assert excinfo.value.translation_placeholders == {"segment_id": "0"}

    # Test segment_id too high
    with pytest.raises(ServiceValidationError) as excinfo:
        await hass.services.async_call(
            DOMAIN,
            "update_time_segment",
            {
                "device_id": device_entry.id,
                "segment_id": 10,
                "start_time": "09:00",
                "end_time": "11:00",
                "batt_mode": "load_first",
                "enabled": True,
            },
            blocking=True,
        )
    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "invalid_segment_id"
    assert excinfo.value.translation_placeholders == {"segment_id": "10"}