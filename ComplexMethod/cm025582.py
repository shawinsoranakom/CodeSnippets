async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ReolinkConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Remove a device from a config entry."""
    host: ReolinkHost = config_entry.runtime_data.host
    (_device_uid, ch, is_chime) = get_device_uid_and_ch(device, host)

    if is_chime:
        await host.api.get_state(cmd="GetDingDongList")
        chime = host.api.chime(ch)
        if (
            chime is None
            or chime.connect_state is None
            or chime.connect_state < 0
            or chime.channel not in host.api.channels
        ):
            _LOGGER.debug(
                "Removing Reolink chime %s with id %s, "
                "since it is not coupled to %s anymore",
                device.name,
                ch,
                host.api.nvr_name,
            )
            return True

        # remove the chime from the host
        await chime.remove()
        await host.api.get_state(cmd="GetDingDongList")
        if chime.connect_state < 0:
            _LOGGER.debug(
                "Removed Reolink chime %s with id %s from %s",
                device.name,
                ch,
                host.api.nvr_name,
            )
            return True

        _LOGGER.warning(
            "Cannot remove Reolink chime %s with id %s, because it is still connected "
            "to %s, please first remove the chime "
            "in the reolink app",
            device.name,
            ch,
            host.api.nvr_name,
        )
        return False

    if not host.api.is_nvr or ch is None:
        _LOGGER.warning(
            "Cannot remove Reolink device %s, because it is not a camera connected "
            "to a NVR/Hub, please remove the integration entry instead",
            device.name,
        )
        return False  # Do not remove the host/NVR itself

    if ch not in host.api.channels:
        _LOGGER.debug(
            "Removing Reolink device %s, "
            "since no camera is connected to NVR channel %s anymore",
            device.name,
            ch,
        )
        return True

    await host.api.get_state(cmd="GetChannelstatus")  # update the camera_online status
    if not host.api.camera_online(ch):
        _LOGGER.debug(
            "Removing Reolink device %s, "
            "since the camera connected to channel %s is offline",
            device.name,
            ch,
        )
        return True

    _LOGGER.warning(
        "Cannot remove Reolink device %s on channel %s, because it is still connected "
        "to the NVR/Hub, please first remove the camera from the NVR/Hub "
        "in the reolink app",
        device.name,
        ch,
    )
    return False