def get_device_list_v1(
    api, config: Mapping[str, str]
) -> tuple[list[dict[str, str]], str]:
    """Device list logic for Open API V1.

    Plant selection is handled in the config flow before this function is called.
    This function expects a specific plant_id and fetches devices for that plant.

    """
    plant_id = config[CONF_PLANT_ID]
    try:
        devices_dict = api.device_list(plant_id)
    except growattServer.GrowattV1ApiError as e:
        if e.error_code == V1_API_ERROR_NO_PRIVILEGE:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for Growatt API: {e.error_msg or str(e)}"
            ) from e
        raise ConfigEntryError(
            f"API error during device list: {e.error_msg or str(e)} (Code: {e.error_code})"
        ) from e
    devices = devices_dict.get("devices", [])
    supported_devices = [
        {
            "deviceSn": device.get("device_sn", ""),
            "deviceType": V1_DEVICE_TYPES[device.get("type")],
        }
        for device in devices
        if device.get("type") in V1_DEVICE_TYPES
    ]

    for device in devices:
        if device.get("type") not in V1_DEVICE_TYPES:
            _LOGGER.warning(
                "Device %s with type %s not supported in Open API V1, skipping",
                device.get("device_sn", ""),
                device.get("type"),
            )
    return supported_devices, plant_id