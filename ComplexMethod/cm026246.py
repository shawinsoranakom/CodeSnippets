def _async_setup_device_registry(
    hass: HomeAssistant, entry: ESPHomeConfigEntry, entry_data: RuntimeEntryData
) -> str:
    """Set up device registry feature for a particular config entry."""
    device_info = entry_data.device_info
    if TYPE_CHECKING:
        assert device_info is not None

    device_registry = dr.async_get(hass)
    # Build sets of valid device identifiers and connections
    valid_connections = {
        (dr.CONNECTION_NETWORK_MAC, format_mac(device_info.mac_address))
    }
    valid_identifiers = {
        (DOMAIN, f"{device_info.mac_address}_{sub_device.device_id}")
        for sub_device in device_info.devices
    }

    # Remove devices that no longer exist
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        # Skip devices we want to keep
        if (
            device.connections & valid_connections
            or device.identifiers & valid_identifiers
        ):
            continue
        # Remove everything else
        device_registry.async_remove_device(device.id)

    sw_version = device_info.esphome_version
    if device_info.compilation_time:
        sw_version += f" ({device_info.compilation_time})"

    configuration_url = None
    if device_info.webserver_port > 0:
        entry_host = entry.data["host"]
        host = f"[{entry_host}]" if ":" in entry_host else entry_host
        configuration_url = f"http://{host}:{device_info.webserver_port}"
    elif (
        (dashboard := async_get_dashboard(hass))
        and dashboard.data
        and dashboard.data.get(device_info.name)
    ):
        configuration_url = f"homeassistant://app/{dashboard.addon_slug}"

    manufacturer = "espressif"
    if device_info.manufacturer:
        manufacturer = device_info.manufacturer
    model = device_info.model
    if device_info.project_name:
        project_name = device_info.project_name.split(".")
        manufacturer = project_name[0]
        model = project_name[1]
        sw_version = (
            f"{device_info.project_version} (ESPHome {device_info.esphome_version})"
        )

    suggested_area: str | None = None
    if device_info.area and device_info.area.name:
        # Prefer device_info.area over suggested_area when area name is not empty
        suggested_area = device_info.area.name
    elif device_info.suggested_area:
        suggested_area = device_info.suggested_area

    # Create/update main device
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        configuration_url=configuration_url,
        connections={(dr.CONNECTION_NETWORK_MAC, device_info.mac_address)},
        name=entry_data.friendly_name or entry_data.name,
        manufacturer=manufacturer,
        model=model,
        sw_version=sw_version,
        suggested_area=suggested_area,
    )

    # Handle sub devices
    # Find available areas from device_info
    areas_by_id = {area.area_id: area for area in device_info.areas}
    # Add the main device's area if it exists
    if device_info.area:
        areas_by_id[device_info.area.area_id] = device_info.area
    # Create/update sub devices that should exist
    for sub_device in device_info.devices:
        # Determine the area for this sub device
        sub_device_suggested_area: str | None = None
        if sub_device.area_id is not None and sub_device.area_id in areas_by_id:
            sub_device_suggested_area = areas_by_id[sub_device.area_id].name

        sub_device_entry = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{device_info.mac_address}_{sub_device.device_id}")},
            name=sub_device.name or device_entry.name,
            manufacturer=manufacturer,
            model=model,
            sw_version=sw_version,
            suggested_area=sub_device_suggested_area,
        )

        # Update the sub device to set via_device_id
        device_registry.async_update_device(
            sub_device_entry.id,
            via_device_id=device_entry.id,
        )

    return device_entry.id