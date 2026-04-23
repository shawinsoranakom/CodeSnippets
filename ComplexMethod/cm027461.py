def __init__(
        self,
        api: SynoApi,
        coordinator: SynologyDSMCentralUpdateCoordinator,
        description: SynologyDSMEntityDescription,
        device_id: str | None = None,
    ) -> None:
        """Initialize the Synology DSM disk or volume entity."""
        super().__init__(api, coordinator, description)
        self._device_id = device_id
        self._device_name: str | None = None
        self._device_manufacturer: str | None = None
        self._device_model: str | None = None
        self._device_firmware: str | None = None
        self._device_type = None
        storage = api.storage
        information = api.information
        network = api.network
        external_usb = api.external_usb
        if TYPE_CHECKING:
            assert information is not None
            assert storage is not None
            assert network is not None

        if "volume" in description.key:
            if TYPE_CHECKING:
                assert self._device_id is not None
            volume = storage.get_volume(self._device_id)
            if TYPE_CHECKING:
                assert volume is not None
            # Volume does not have a name
            self._device_name = volume["id"].replace("_", " ").capitalize()
            self._device_manufacturer = "Synology"
            self._device_model = information.model
            self._device_firmware = information.version_string
            self._device_type = (
                volume["device_type"]
                .replace("_", " ")
                .replace("raid", "RAID")
                .replace("shr", "SHR")
            )
        elif "disk" in description.key:
            if TYPE_CHECKING:
                assert self._device_id is not None
            disk = storage.get_disk(self._device_id)
            if TYPE_CHECKING:
                assert disk is not None
            self._device_name = disk["name"]
            self._device_manufacturer = disk["vendor"]
            self._device_model = disk["model"].strip()
            self._device_firmware = disk["firm"]
            self._device_type = disk["diskType"]
        elif "device" in description.key:
            if TYPE_CHECKING:
                assert self._device_id is not None
                assert external_usb is not None
            for device in external_usb.get_devices.values():
                if device.device_name == self._device_id:
                    self._device_name = device.device_name
                    self._device_manufacturer = device.device_manufacturer
                    self._device_model = device.device_product_name
                    self._device_type = device.device_type
                    break
        elif "partition" in description.key:
            if TYPE_CHECKING:
                assert self._device_id is not None
                assert external_usb is not None
            for device in external_usb.get_devices.values():
                for partition in device.device_partitions.values():
                    if partition.partition_title == self._device_id:
                        self._device_name = partition.partition_title
                        self._device_manufacturer = "Synology"
                        self._device_model = partition.filesystem
                        break

        self._attr_unique_id += f"_{self._device_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{information.serial}_{self._device_id}")},
            name=f"{network.hostname} ({self._device_name})",
            manufacturer=self._device_manufacturer,
            model=self._device_model,
            sw_version=self._device_firmware,
            via_device=(DOMAIN, information.serial),
            configuration_url=self._api.config_url,
        )