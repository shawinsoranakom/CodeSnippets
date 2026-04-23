async def test_external_usb(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    setup_dsm_with_usb: MagicMock,
) -> None:
    """Test Synology DSM USB sensors."""
    # test disabled device size sensor
    entity_id = "sensor.nas_meontheinternet_com_usb_disk_1_device_size"
    entity_entry = entity_registry.async_get(entity_id)

    assert entity_entry
    assert entity_entry.disabled
    assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # test partition size sensor
    sensor = hass.states.get(
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_size"
    )
    assert sensor is not None
    assert sensor.state == "14901.998046875"
    assert (
        sensor.attributes["friendly_name"]
        == "nas.meontheinternet.com (USB Disk 1 Partition 1) Partition size"
    )
    assert sensor.attributes["device_class"] == "data_size"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "GiB"
    assert sensor.attributes["attribution"] == "Data provided by Synology"

    # test partition used space sensor
    sensor = hass.states.get(
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_used_space"
    )
    assert sensor is not None
    assert sensor.state == "5803.1650390625"
    assert (
        sensor.attributes["friendly_name"]
        == "nas.meontheinternet.com (USB Disk 1 Partition 1) Partition used space"
    )
    assert sensor.attributes["device_class"] == "data_size"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "GiB"
    assert sensor.attributes["attribution"] == "Data provided by Synology"

    # test partition used sensor
    sensor = hass.states.get(
        "sensor.nas_meontheinternet_com_usb_disk_1_partition_1_partition_used"
    )
    assert sensor is not None
    assert sensor.state == "38.9"
    assert (
        sensor.attributes["friendly_name"]
        == "nas.meontheinternet.com (USB Disk 1 Partition 1) Partition used"
    )
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "%"
    assert sensor.attributes["attribution"] == "Data provided by Synology"