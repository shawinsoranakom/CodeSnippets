async def test_device_registry_bridge(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test bridge devices are set up correctly with via_device."""
    # Validate bridge
    bridge_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "mock-hub-id")}
    )
    assert bridge_entry is not None

    assert bridge_entry.name == "My Mock Bridge"
    assert bridge_entry.manufacturer == "Mock Vendor"
    assert bridge_entry.model == "Mock Bridge"
    assert bridge_entry.hw_version == "TEST_VERSION"
    assert bridge_entry.sw_version == "123.4.5"

    # Device 1
    device1_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "mock-id-kitchen-ceiling")}
    )
    assert device1_entry is not None

    assert device1_entry.via_device_id == bridge_entry.id
    assert device1_entry.name == "Kitchen Ceiling"
    assert device1_entry.manufacturer == "Mock Vendor"
    assert device1_entry.model == "Mock Light"
    assert device1_entry.hw_version is None
    assert device1_entry.sw_version == "67.8.9"

    # Device 2
    device2_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "mock-id-living-room-ceiling")}
    )
    assert device2_entry is not None

    assert device2_entry.via_device_id == bridge_entry.id
    assert device2_entry.name == "Living Room Ceiling"
    assert device2_entry.manufacturer == "Mock Vendor"
    assert device2_entry.model == "Mock Light"
    assert device2_entry.hw_version is None
    assert device2_entry.sw_version == "1.49.1"