def __init__(
        self,
        reolink_data: ReolinkData,
        channel: int,
        coordinator: ReolinkCoordinator | None = None,
    ) -> None:
        """Initialize ReolinkChannelCoordinatorEntity for a hardware camera connected to a channel of the NVR."""
        super().__init__(reolink_data, coordinator)

        self._channel = channel
        if self._host.api.is_nvr and self._host.api.supported(channel, "UID"):
            self._attr_unique_id = f"{self._host.unique_id}_{self._host.api.camera_uid(channel)}_{self.entity_description.key}"
        else:
            self._attr_unique_id = (
                f"{self._host.unique_id}_{channel}_{self.entity_description.key}"
            )

        dev_ch = channel
        if self._host.api.model in DUAL_LENS_MODELS:
            dev_ch = 0

        if self._host.api.is_nvr:
            if self._host.api.supported(dev_ch, "UID"):
                self._dev_id = (
                    f"{self._host.unique_id}_{self._host.api.camera_uid(dev_ch)}"
                )
            else:
                self._dev_id = f"{self._host.unique_id}_ch{dev_ch}"

            connections = set()
            if mac := self._host.api.baichuan.mac_address(dev_ch):
                connections.add((CONNECTION_NETWORK_MAC, mac))

            if self._conf_url is None:
                conf_url = None
            else:
                conf_url = f"{self._conf_url}/?ch={dev_ch}"

            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, self._dev_id)},
                connections=connections,
                via_device=(DOMAIN, self._host.unique_id),
                name=self._host.api.camera_name(dev_ch),
                model=self._host.api.camera_model(dev_ch),
                model_id=self._host.api.item_number(dev_ch),
                manufacturer=self._host.api.manufacturer,
                hw_version=self._host.api.camera_hardware_version(dev_ch),
                sw_version=self._host.api.camera_sw_version(dev_ch),
                serial_number=self._host.api.camera_uid(dev_ch),
                configuration_url=conf_url,
            )