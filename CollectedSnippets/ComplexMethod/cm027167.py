def device_info(self) -> DeviceInfo:
        """Get a an HA device representing this Bond controlled device."""
        device_info = DeviceInfo(
            manufacturer=self._hub.make,
            # type ignore: tuple items should not be Optional
            identifiers={(DOMAIN, self._hub.bond_id, self._device_id)},  # type: ignore[arg-type]
            configuration_url=f"http://{self._hub.host}",
        )
        if self.name is not None:
            device_info[ATTR_NAME] = self._device.name
        if self._hub.bond_id is not None:
            device_info[ATTR_VIA_DEVICE] = (DOMAIN, self._hub.bond_id)
        if self._device.location is not None:
            device_info[ATTR_SUGGESTED_AREA] = self._device.location
        if not self._hub.is_bridge:
            if self._hub.model is not None:
                device_info[ATTR_MODEL] = self._hub.model
            if self._hub.fw_ver is not None:
                device_info[ATTR_SW_VERSION] = self._hub.fw_ver
            if self._hub.mcu_ver is not None:
                device_info[ATTR_HW_VERSION] = self._hub.mcu_ver
        else:
            model_data = []
            if self._device.branding_profile:
                model_data.append(self._device.branding_profile)
            if self._device.template:
                model_data.append(self._device.template)
            if model_data:
                device_info[ATTR_MODEL] = " ".join(model_data)

        return device_info