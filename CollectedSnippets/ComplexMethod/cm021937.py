def create_tibber_device(
    device_id: str = "device-id",
    external_id: str = "external-id",
    name: str = "Test Device",
    brand: str = "Tibber",
    model: str = "Gen1",
    home_id: str = "home-id",
    state_of_charge: float | None = None,
    connector_status: str | None = None,
    charging_status: str | None = None,
    device_status: str | None = None,
    is_online: str | None = None,
    sensor_values: dict[str, Any] | None = None,
) -> tibber.data_api.TibberDevice:
    """Create a fake Tibber Data API device.

    Args:
        device_id: Device ID.
        external_id: External device ID.
        name: Device name.
        brand: Device brand.
        model: Device model.
        home_id: Home ID.
        state_of_charge: Battery state of charge (for regular sensors).
        connector_status: Connector status (for binary sensors).
        charging_status: Charging status (for binary sensors).
        device_status: Device on/off status (for binary sensors).
        is_online: Device online status (for binary sensors).
        sensor_values: Dictionary mapping sensor IDs to their values for additional sensors.
    """
    capabilities = []

    # Add regular sensor capabilities
    if state_of_charge is not None:
        capabilities.append(
            {
                "id": "storage.stateOfCharge",
                "value": state_of_charge,
                "description": "State of charge",
                "unit": "%",
            }
        )
        capabilities.append(
            {
                "id": "unknown.sensor.id",
                "value": None,
                "description": "Unknown",
                "unit": "",
            }
        )

    if connector_status is not None:
        capabilities.append(
            {
                "id": "connector.status",
                "value": connector_status,
                "description": "Connector status",
                "unit": "",
            }
        )

    if charging_status is not None:
        capabilities.append(
            {
                "id": "charging.status",
                "value": charging_status,
                "description": "Charging status",
                "unit": "",
            }
        )

    if device_status is not None:
        capabilities.append(
            {
                "id": "onOff",
                "value": device_status,
                "description": "Device status",
                "unit": "",
            }
        )

    if is_online is not None:
        capabilities.append(
            {
                "id": "isOnline",
                "value": is_online,
                "description": "Device online status",
                "unit": "",
            }
        )

    if sensor_values:
        for sensor_id, value in sensor_values.items():
            capabilities.append(
                {
                    "id": sensor_id,
                    "value": value,
                    "description": sensor_id.replace(".", " ").title(),
                    "unit": "",
                }
            )

    device_data = {
        "id": device_id,
        "externalId": external_id,
        "info": {
            "name": name,
            "brand": brand,
            "model": model,
        },
        "capabilities": capabilities,
    }
    return tibber.data_api.TibberDevice(device_data, home_id=home_id)