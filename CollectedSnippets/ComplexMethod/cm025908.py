def _async_device_entry_to_keep(
    old_entry: dr.DeviceEntry, new_entry: dr.DeviceEntry
) -> dr.DeviceEntry:
    """Determine which device entry to keep when there are duplicates.

    As we transitioned to new unique ids, we did not update existing device entries
    and as a result there are devices with both the old and new unique id format. We
    have to pick which one to keep, and preferably this can repair things if the
    user previously renamed devices.
    """
    # Prefer the new device if the user already gave it a name or area. Otherwise,
    # do the same for the old entry. If no entries have been modified then keep the new one.
    if new_entry.disabled_by is None and (
        new_entry.area_id is not None or new_entry.name_by_user is not None
    ):
        return new_entry
    if old_entry.disabled_by is None and (
        old_entry.area_id is not None or old_entry.name_by_user is not None
    ):
        return old_entry
    return new_entry if new_entry.disabled_by is None else old_entry