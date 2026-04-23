def create_devices(
    device_registry: dr.DeviceRegistry,
    devices: dict[str, FullDevice],
    entry: SmartThingsConfigEntry,
    rooms: dict[str, str],
) -> None:
    """Create devices in the device registry."""
    for device in sorted(
        devices.values(), key=lambda d: d.device.parent_device_id or ""
    ):
        kwargs: dict[str, Any] = {}
        if device.device.hub is not None:
            kwargs = {
                ATTR_SW_VERSION: device.device.hub.firmware_version,
                ATTR_MODEL: device.device.hub.hardware_type,
            }
            if device.device.hub.mac_address:
                kwargs[ATTR_CONNECTIONS] = {
                    (dr.CONNECTION_NETWORK_MAC, device.device.hub.mac_address)
                }
            if device.device.hub.hub_eui:
                connections = kwargs.setdefault(ATTR_CONNECTIONS, set())
                connections.add(
                    (
                        dr.CONNECTION_ZIGBEE,
                        format_zigbee_address(device.device.hub.hub_eui),
                    )
                )
        if device.device.parent_device_id and device.device.parent_device_id in devices:
            kwargs[ATTR_VIA_DEVICE] = (DOMAIN, device.device.parent_device_id)
        if (ocf := device.device.ocf) is not None:
            kwargs.update(
                {
                    ATTR_MANUFACTURER: ocf.manufacturer_name,
                    ATTR_MODEL_ID: ocf.model_code,
                    ATTR_MODEL: (
                        (ocf.model_number.split("|")[0]) if ocf.model_number else None
                    ),
                    ATTR_HW_VERSION: ocf.hardware_version,
                    ATTR_SW_VERSION: ocf.firmware_version,
                }
            )
        if (viper := device.device.viper) is not None:
            kwargs.update(
                {
                    ATTR_MANUFACTURER: viper.manufacturer_name,
                    ATTR_MODEL: viper.model_name,
                    ATTR_HW_VERSION: viper.hardware_version,
                    ATTR_SW_VERSION: viper.software_version,
                }
            )
        if (zigbee := device.device.zigbee) is not None:
            kwargs[ATTR_CONNECTIONS] = {
                (dr.CONNECTION_ZIGBEE, format_zigbee_address(zigbee.eui))
            }
        if (matter := device.device.matter) is not None:
            kwargs.update(
                {
                    ATTR_HW_VERSION: matter.hardware_version,
                    ATTR_SW_VERSION: matter.software_version,
                    ATTR_SERIAL_NUMBER: matter.serial_number,
                }
            )
        if (main_component := device.status.get(MAIN)) is not None:
            if (
                device_identification := main_component.get(
                    Capability.SAMSUNG_CE_DEVICE_IDENTIFICATION
                )
            ) is not None:
                new_kwargs = {
                    ATTR_SERIAL_NUMBER: device_identification[
                        Attribute.SERIAL_NUMBER
                    ].value
                }
                if ATTR_MODEL_ID not in kwargs:
                    new_kwargs[ATTR_MODEL_ID] = device_identification[
                        Attribute.MODEL_NAME
                    ].value
                kwargs.update(new_kwargs)
            if (
                device_status := main_component.get(Capability.SAMSUNG_IM_DEVICESTATUS)
            ) is not None:
                mac_connections: set[tuple[str, str]] = set()
                status = cast(dict[str, str], device_status[Attribute.STATUS].value)
                if wifi_mac := status.get("wifiMac"):
                    mac_connections.add((dr.CONNECTION_NETWORK_MAC, wifi_mac))
                if bluetooth_address := status.get("btAddr"):
                    mac_connections.add(
                        (dr.CONNECTION_BLUETOOTH, bluetooth_address.lower())
                    )
                if mac_connections:
                    kwargs.setdefault(ATTR_CONNECTIONS, set()).update(mac_connections)
        if (
            device_registry.async_get_device({(DOMAIN, device.device.device_id)})
            is None
        ):
            kwargs.update(
                {
                    ATTR_SUGGESTED_AREA: (
                        rooms.get(device.device.room_id)
                        if device.device.room_id
                        else None
                    )
                }
            )
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device.device.device_id)},
            configuration_url="https://account.smartthings.com",
            name=device.device.label,
            **kwargs,
        )