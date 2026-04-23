async def test_external_usb_new_device(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    setup_dsm_with_usb: MagicMock,
) -> None:
    """Test Synology DSM USB adding new device."""

    expected_sensors_disk_1 = {
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
    expected_sensors_disk_2 = {
        "sensor.nas_meontheinternet_com_usb_disk_2_status": ("normal", {}),
        "sensor.nas_meontheinternet_com_usb_disk_2_partition_1_partition_size": (
            "14901.998046875",
            {
                "device_class": "data_size",
                "state_class": "measurement",
                "unit_of_measurement": "GiB",
                "attribution": "Data provided by Synology",
            },
        ),
        "sensor.nas_meontheinternet_com_usb_disk_2_partition_1_partition_used_space": (
            "5803.1650390625",
            {
                "device_class": "data_size",
                "state_class": "measurement",
                "unit_of_measurement": "GiB",
                "attribution": "Data provided by Synology",
            },
        ),
        "sensor.nas_meontheinternet_com_usb_disk_2_partition_1_partition_used": (
            "38.9",
            {
                "state_class": "measurement",
                "unit_of_measurement": "%",
                "attribution": "Data provided by Synology",
            },
        ),
    }

    # Initial check of existing sensors
    for sensor_id, (expected_state, expected_attrs) in expected_sensors_disk_1.items():
        sensor = hass.states.get(sensor_id)
        assert sensor is not None
        assert sensor.state == expected_state
        for attr_key, attr_value in expected_attrs.items():
            assert sensor.attributes[attr_key] == attr_value
    for sensor_id in expected_sensors_disk_2:
        assert hass.states.get(sensor_id) is None

    # Mock the get_devices method to simulate a USB disk being added
    setup_dsm_with_usb.external_usb.get_devices = mock_dsm_external_usb_devices_usb2()
    # Coordinator refresh
    await setup_dsm_with_usb.mock_entry.runtime_data.coordinator_central.async_request_refresh()
    await hass.async_block_till_done()

    for sensor_id, (expected_state, expected_attrs) in chain(
        expected_sensors_disk_1.items(), expected_sensors_disk_2.items()
    ):
        sensor = hass.states.get(sensor_id)
        assert sensor is not None
        assert sensor.state == expected_state
        for attr_key, attr_value in expected_attrs.items():
            assert sensor.attributes[attr_key] == attr_value