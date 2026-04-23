def get_device_uid_and_ch(
    device: dr.DeviceEntry | tuple[str, str], host: ReolinkHost
) -> tuple[list[str], int | None, bool]:
    """Get the channel and the split device_uid from a reolink DeviceEntry."""
    device_uid = []
    is_chime = False

    if isinstance(device, dr.DeviceEntry):
        dev_ids = device.identifiers
    else:
        dev_ids = {device}

    for dev_id in dev_ids:
        if dev_id[0] == DOMAIN:
            device_uid = dev_id[1].split("_")
            if device_uid[0] == host.unique_id:
                break

    if len(device_uid) < 2:
        # NVR itself
        ch = None
    elif device_uid[1].startswith("ch") and len(device_uid[1]) <= 5:
        ch = int(device_uid[1][2:])
    elif device_uid[1].startswith("chime"):
        ch = int(device_uid[1][5:])
        is_chime = True
    else:
        device_uid_part = "_".join(device_uid[1:])
        ch = host.api.channel_for_uid(device_uid_part)
    return (device_uid, ch, is_chime)