def ble_device_matches(
    matcher: BluetoothMatcherOptional,
    service_info: BluetoothServiceInfoBleak,
) -> bool:
    """Check if a ble device and advertisement_data matches the matcher."""
    # Don't check address here since all callers already
    # check the address and we don't want to double check
    # since it would result in an unreachable reject case.
    if matcher.get(CONNECTABLE, True) and not service_info.connectable:
        return False

    if (
        service_uuid := matcher.get(SERVICE_UUID)
    ) and service_uuid not in service_info.service_uuids:
        return False

    if (
        service_data_uuid := matcher.get(SERVICE_DATA_UUID)
    ) and service_data_uuid not in service_info.service_data:
        return False

    if (manufacturer_id := matcher.get(MANUFACTURER_ID)) is not None:
        if manufacturer_id not in service_info.manufacturer_data:
            return False

        if manufacturer_data_start := matcher.get(MANUFACTURER_DATA_START):
            if not service_info.manufacturer_data[manufacturer_id].startswith(
                bytes(manufacturer_data_start)
            ):
                return False

    if (local_name := matcher.get(LOCAL_NAME)) and not _memorized_fnmatch(
        service_info.name,
        local_name,
    ):
        return False

    return True