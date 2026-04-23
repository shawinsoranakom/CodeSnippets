async def test_sub_device_references_main_device_area(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test sub devices can reference the main device's area."""
    device_registry = dr.async_get(hass)

    # Define areas - note we don't include area_id=0 in the areas list
    areas = [
        AreaInfo(area_id=1, name="Living Room"),
        AreaInfo(area_id=2, name="Bedroom"),
    ]

    # Define sub devices - one references the main device's area (area_id=0)
    sub_devices = [
        SubDeviceInfo(
            device_id=11111111, name="Motion Sensor", area_id=0
        ),  # Main device area
        SubDeviceInfo(
            device_id=22222222, name="Light Switch", area_id=1
        ),  # Living Room
        SubDeviceInfo(
            device_id=33333333, name="Temperature Sensor", area_id=2
        ),  # Bedroom
    ]

    device_info = {
        "areas": areas,
        "devices": sub_devices,
        "area": AreaInfo(area_id=0, name="Main Hub Area"),
    }

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
    )

    # Check main device has correct area
    main_device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device.device_info.mac_address)}
    )
    assert main_device is not None
    assert (
        main_device.area_id == area_registry.async_get_area_by_name("Main Hub Area").id
    )

    # Check sub device 1 uses main device's area
    sub_device_1 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_11111111")}
    )
    assert sub_device_1 is not None
    assert (
        sub_device_1.area_id == area_registry.async_get_area_by_name("Main Hub Area").id
    )

    # Check sub device 2 uses Living Room
    sub_device_2 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_22222222")}
    )
    assert sub_device_2 is not None
    assert (
        sub_device_2.area_id == area_registry.async_get_area_by_name("Living Room").id
    )

    # Check sub device 3 uses Bedroom
    sub_device_3 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_33333333")}
    )
    assert sub_device_3 is not None
    assert sub_device_3.area_id == area_registry.async_get_area_by_name("Bedroom").id