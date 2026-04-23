async def test_sub_device_creation(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test sub devices are created in device registry."""
    device_registry = dr.async_get(hass)

    # Define areas
    areas = [
        AreaInfo(area_id=1, name="Living Room"),
        AreaInfo(area_id=2, name="Bedroom"),
        AreaInfo(area_id=3, name="Kitchen"),
    ]

    # Define sub devices
    sub_devices = [
        SubDeviceInfo(device_id=11111111, name="Motion Sensor", area_id=1),
        SubDeviceInfo(device_id=22222222, name="Light Switch", area_id=1),
        SubDeviceInfo(device_id=33333333, name="Temperature Sensor", area_id=2),
    ]

    device_info = {
        "areas": areas,
        "devices": sub_devices,
        "area": AreaInfo(area_id=0, name="Main Hub"),
    }

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
    )

    # Check main device is created
    main_device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device.device_info.mac_address)}
    )
    assert main_device is not None
    assert main_device.area_id == area_registry.async_get_area_by_name("Main Hub").id

    # Check sub devices are created
    sub_device_1 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_11111111")}
    )
    assert sub_device_1 is not None
    assert sub_device_1.name == "Motion Sensor"
    assert (
        sub_device_1.area_id == area_registry.async_get_area_by_name("Living Room").id
    )
    assert sub_device_1.via_device_id == main_device.id

    sub_device_2 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_22222222")}
    )
    assert sub_device_2 is not None
    assert sub_device_2.name == "Light Switch"
    assert (
        sub_device_2.area_id == area_registry.async_get_area_by_name("Living Room").id
    )
    assert sub_device_2.via_device_id == main_device.id

    sub_device_3 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_33333333")}
    )
    assert sub_device_3 is not None
    assert sub_device_3.name == "Temperature Sensor"
    assert sub_device_3.area_id == area_registry.async_get_area_by_name("Bedroom").id
    assert sub_device_3.via_device_id == main_device.id