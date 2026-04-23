async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: SynologyDSMConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove synology_dsm config entry from a device."""
    data = entry.runtime_data
    api = data.api
    if TYPE_CHECKING:
        assert api.information is not None
    serial = api.information.serial
    storage = api.storage
    if TYPE_CHECKING:
        assert storage is not None
    all_cameras: list[SynoCamera] = []
    if api.surveillance_station is not None:
        # get_all_cameras does not do I/O
        all_cameras = api.surveillance_station.get_all_cameras()
    device_ids = chain(
        (camera.id for camera in all_cameras),
        storage.volumes_ids,
        storage.disks_ids,
        storage.volumes_ids,
        (SynoSurveillanceStation.INFO_API_KEY,),  # Camera home/away
    )
    return not device_entry.identifiers.intersection(
        (
            (DOMAIN, serial),  # Base device
            *(
                (DOMAIN, f"{serial}_{device_id}") for device_id in device_ids
            ),  # Storage and cameras
        )
    )