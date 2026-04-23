def get_all_disk_mounts(
    hass: HomeAssistant, psutil_wrapper: ha_psutil.PsutilWrapper
) -> set[str]:
    """Return all disk mount points on system."""
    disks: set[str] = set()
    for part in psutil_wrapper.psutil.disk_partitions(all=True):
        if part.fstype in SKIP_DISK_TYPES:
            # Ignore disks which are memory
            continue
        try:
            if not os.path.isdir(part.mountpoint):
                _LOGGER.debug(
                    "Mountpoint %s was excluded because it is not a directory",
                    part.mountpoint,
                )
                continue
            usage = psutil_wrapper.psutil.disk_usage(part.mountpoint)
        except PermissionError:
            _LOGGER.debug(
                "No permission for running user to access %s", part.mountpoint
            )
            continue
        except OSError as err:
            _LOGGER.debug(
                "Mountpoint %s was excluded because of: %s", part.mountpoint, err
            )
            continue
        if usage.total > 0 and part.device != "":
            disks.add(part.mountpoint)
    _LOGGER.debug("Adding disks: %s", ", ".join(disks))
    return disks