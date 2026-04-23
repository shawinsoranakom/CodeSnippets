async def async_get_usb_ports(hass: HomeAssistant) -> dict[str, str]:
    """Return a dict of USB ports and their friendly names."""
    port_descriptions = {}
    for port in await usb.async_scan_serial_ports(hass):
        if (port.manufacturer, port.description) in IGNORED_USB_DEVICES:
            continue

        human_name = usb.human_readable_device_name(
            port.device,
            port.serial_number,
            port.manufacturer,
            port.description,
            port.vid if isinstance(port, usb.USBDevice) else None,
            port.pid if isinstance(port, usb.USBDevice) else None,
        )
        port_descriptions[port.device] = human_name

    # Filter out "n/a" descriptions only if there are other ports available
    non_na_ports = {
        path: desc
        for path, desc in port_descriptions.items()
        if not desc.lower().startswith("n/a")
    }

    # If we have non-"n/a" ports, return only those; otherwise return all ports as-is
    return non_na_ports or port_descriptions