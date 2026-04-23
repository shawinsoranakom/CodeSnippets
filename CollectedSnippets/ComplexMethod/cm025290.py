async def async_update_device_config(
    device_connection: DeviceConnection, device_config: ConfigType
) -> None:
    """Fill missing values in device_config with infos from LCN bus."""
    # fetch serial info if device is module
    if not (is_group := device_config[CONF_ADDRESS][2]):  # is module
        await device_connection.serials_known()
        if device_config[CONF_HARDWARE_SERIAL] == -1:
            device_config[CONF_HARDWARE_SERIAL] = (
                device_connection.serials.hardware_serial
            )
        if device_config[CONF_SOFTWARE_SERIAL] == -1:
            device_config[CONF_SOFTWARE_SERIAL] = (
                device_connection.serials.software_serial
            )
        if device_config[CONF_HARDWARE_TYPE] == -1:
            device_config[CONF_HARDWARE_TYPE] = (
                device_connection.serials.hardware_type.value
            )

    # fetch name if device is module
    if device_config[CONF_NAME] != "":
        return

    device_name: str | None = None
    if not is_group:
        device_name = await device_connection.request_name()
    if is_group or device_name is None:
        module_type = "Group" if is_group else "Module"
        device_name = (
            f"{module_type} "
            f"{device_config[CONF_ADDRESS][0]:03d}/"
            f"{device_config[CONF_ADDRESS][1]:03d}"
        )
    device_config[CONF_NAME] = device_name