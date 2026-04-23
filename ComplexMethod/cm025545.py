def usb_device_matches_matcher(device: USBDevice, matcher: USBMatcher) -> bool:
    """Check if a USB device matches a USB matcher."""
    if "vid" in matcher and device.vid != matcher["vid"]:
        return False

    if "pid" in matcher and device.pid != matcher["pid"]:
        return False

    if "serial_number" in matcher and not _fnmatch_lower(
        device.serial_number, matcher["serial_number"]
    ):
        return False

    if "manufacturer" in matcher and not _fnmatch_lower(
        device.manufacturer, matcher["manufacturer"]
    ):
        return False

    if "description" in matcher and not _fnmatch_lower(
        device.description, matcher["description"]
    ):
        return False

    return True