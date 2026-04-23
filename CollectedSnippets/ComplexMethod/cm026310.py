def _async_update_device_from_protect(self, device: ProtectDeviceType) -> None:
        """Update Entity object from Protect device."""
        was_available = self._attr_available
        if last_updated_success := self.data.last_update_success:
            self.device = device

        if device.model is ModelType.NVR:
            available = last_updated_success
        else:
            if TYPE_CHECKING:
                assert isinstance(device, ProtectAdoptableDeviceModel)
            connected = device.state is StateType.CONNECTED or (
                not device.is_adopted_by_us and device.can_adopt
            )
            async_get_ufp_enabled = self._async_get_ufp_enabled
            enabled = not async_get_ufp_enabled or async_get_ufp_enabled(device)
            available = last_updated_success and connected and enabled

        if available != was_available:
            self._attr_available = available