def get_rpc_sub_device_name(
    device: RpcDevice, key: str, emeter_phase: str | None = None
) -> str:
    """Get name based on device and channel name."""
    if key in device.config and key != "em:0":
        # workaround for Pro 3EM, we don't want to get name for em:0
        if (zone_id := get_irrigation_zone_id(device, key)) is not None:
            # workaround for Irrigation controller, name stored in "service:0"
            if zone_name := device.config["service:0"]["zones"][zone_id]["name"]:
                return cast(str, zone_name)

        if entity_name := device.config[key].get("name"):
            return cast(str, entity_name)

    _, component, component_id = get_rpc_key(get_rpc_key_normalized(key))

    if component in ("cct", "rgb", "rgbw"):
        return f"{device.name} {component.upper()} light {component_id}"
    if component == "em1":
        return f"{device.name} Energy Meter {component_id}"
    if component == "em" and emeter_phase is not None:
        return f"{device.name} Phase {emeter_phase}"
    if component == "switch":
        return f"{device.name} Output {component_id}"

    return f"{device.name} {component.title()} {component_id}"