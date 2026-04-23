async def test_device_registry_single_node_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    unique_id: str,
    name: str,
) -> None:
    """Test bridge devices are set up correctly with via_device."""
    entry = device_registry.async_get_device(
        identifiers={
            (DOMAIN, f"deviceid_00000000000004D2-{unique_id}-MatterNodeDevice")
        }
    )
    assert entry is not None

    # test serial id present as additional identifier
    assert (DOMAIN, "serial_12345678") in entry.identifiers

    assert entry.name == name
    assert entry.manufacturer == "Nabu Casa"
    assert entry.model == "Mock Light"
    assert entry.model_id == "32768"
    assert entry.hw_version == "v1.0"
    assert entry.sw_version == "v1.0"
    assert entry.serial_number == "12345678"