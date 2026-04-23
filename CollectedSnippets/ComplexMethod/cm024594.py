async def test_external_usb_availability(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    setup_dsm_with_usb: MagicMock,
) -> None:
    """Test Synology DSM USB availability."""

    expected_sensors_disk_1_available = {
        "sensor.nas_meontheinternet_com_usb_disk_1_status": ("normal", {}),
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_size": (
            "14901.998046875",
            {},
        ),
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_used_space": (
            "5803.1650390625",
            {},
        ),
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_used": (
            "38.9",
            {},
        ),
    }
    expected_sensors_disk_1_unavailable = {
        "sensor.nas_meontheinternet_com_usb_disk_1_status": ("unavailable", {}),
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_size": (
            "unavailable",
            {},
        ),
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_used_space": (
            "unavailable",
            {},
        ),
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_used": (
            "unavailable",
            {},
        ),
    }

    # Initial check of existing sensors
    for sensor_id, (
        expected_state,
        expected_attrs,
    ) in expected_sensors_disk_1_available.items():
        sensor = hass.states.get(sensor_id)
        assert sensor is not None
        assert sensor.state == expected_state
        for attr_key, attr_value in expected_attrs.items():
            assert sensor.attributes[attr_key] == attr_value

    # Mock the get_devices method to simulate no USB devices being connected
    setup_dsm_with_usb.external_usb.get_devices = mock_dsm_external_usb_devices_usb0()
    # Coordinator refresh
    await setup_dsm_with_usb.mock_entry.runtime_data.coordinator_central.async_request_refresh()
    await hass.async_block_till_done()

    for sensor_id, (
        expected_state,
        expected_attrs,
    ) in expected_sensors_disk_1_unavailable.items():
        sensor = hass.states.get(sensor_id)
        assert sensor is not None
        assert sensor.state == expected_state
        for attr_key, attr_value in expected_attrs.items():
            assert sensor.attributes[attr_key] == attr_value