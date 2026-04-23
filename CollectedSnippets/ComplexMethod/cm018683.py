def fake_devices_fixture() -> list[FakeDevice]:
    """Fixture to mock the device manager."""
    devices = []
    for device_data, device_product_data in HOME_DATA.device_products.values():
        fake_device = FakeDevice(
            device_info=deepcopy(device_data),
            product=deepcopy(device_product_data),
        )
        fake_device.is_connected = True
        fake_device.is_local_connected = True
        if device_data.pv == "1.0":
            fake_device.v1_properties = create_v1_properties(
                NETWORK_INFO_BY_DEVICE[device_data.duid]
            )
        elif device_data.pv == "A01":
            if device_product_data.category == RoborockCategory.WET_DRY_VAC:
                fake_device.dyad = create_dyad_trait()
            elif device_product_data.category == RoborockCategory.WASHING_MACHINE:
                fake_device.zeo = create_zeo_trait()
            else:
                raise ValueError("Unknown A01 category in test HOME_DATA")
        elif device_data.pv == "B01":
            if device_product_data.model == "roborock.vacuum.ss07":
                fake_device.b01_q10_properties = create_b01_q10_trait()
            else:
                fake_device.b01_q7_properties = create_b01_q7_trait()
        else:
            raise ValueError("Unknown pv in test HOME_DATA")
        devices.append(fake_device)
    return devices