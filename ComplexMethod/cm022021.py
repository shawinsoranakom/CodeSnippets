async def create_device(hass: HomeAssistant, mock_device_code: str) -> CustomerDevice:
    """Create a CustomerDevice for testing."""
    details = await async_load_json_object_fixture(
        hass, f"{mock_device_code}.json", DOMAIN
    )
    device = MagicMock(spec=CustomerDevice)

    # Use reverse of the product_id for testing
    device.id = mock_device_code.replace("_", "")[::-1]

    device.name = details["name"]
    device.category = details["category"]
    device.product_id = details["product_id"]
    device.product_name = details["product_name"]
    device.online = details["online"]
    device.sub = details.get("sub")
    device.time_zone = details.get("time_zone")
    device.active_time = details.get("active_time")
    if device.active_time:
        device.active_time = int(dt_util.as_timestamp(device.active_time))
    device.create_time = details.get("create_time")
    if device.create_time:
        device.create_time = int(dt_util.as_timestamp(device.create_time))
    device.update_time = details.get("update_time")
    if device.update_time:
        device.update_time = int(dt_util.as_timestamp(device.update_time))
    device.support_local = details.get("support_local")
    device.local_strategy = details.get("local_strategy")
    device.mqtt_connected = details.get("mqtt_connected")

    device.function = {
        key: DeviceFunction(
            code=key,
            type=value["type"],
            values=(
                values
                if isinstance(values := value["value"], str)
                else json_dumps(values)
            ),
        )
        for key, value in details["function"].items()
    }
    device.status_range = {
        key: DeviceStatusRange(
            code=key,
            report_type=value.get("report_type"),
            type=value["type"],
            values=(
                values
                if isinstance(values := value["value"], str)
                else json_dumps(values)
            ),
        )
        for key, value in details["status_range"].items()
    }
    device.status = details["status"]
    for key, value in device.status.items():
        # Some devices do not provide a status_range for all status DPs
        # Others set the type as String in status_range and as Json in function
        if ((dp_type := device.status_range.get(key)) and dp_type.type == "Json") or (
            (dp_type := device.function.get(key)) and dp_type.type == "Json"
        ):
            device.status[key] = json_dumps(value)
        if value == "**REDACTED**":
            # It was redacted, which may cause issue with b64decode
            device.status[key] = ""
    return device