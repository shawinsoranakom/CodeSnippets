def get_node_from_device_entry(
    hass: HomeAssistant, device: dr.DeviceEntry
) -> MatterNode | None:
    """Return MatterNode from device entry."""
    matter = get_matter(hass)
    device_id_type_prefix = f"{ID_TYPE_DEVICE_ID}_"
    device_id_full = next(
        (
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
            and identifier[1].startswith(device_id_type_prefix)
        ),
        None,
    )

    if device_id_full is None:
        return None

    device_id = device_id_full.lstrip(device_id_type_prefix)
    matter_client = matter.matter_client
    server_info = matter_client.server_info

    if server_info is None:
        raise RuntimeError("Matter server information is not available")

    return next(
        (
            node
            for node in matter_client.get_nodes()
            for endpoint in node.endpoints.values()
            if get_device_id(server_info, endpoint) == device_id
        ),
        None,
    )