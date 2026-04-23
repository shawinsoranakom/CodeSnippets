def init_base(self) -> None:
        """Initialize common attributes - may be based on xknx device instance."""
        _supports_tilt = False
        self._attr_supported_features = (
            CoverEntityFeature.CLOSE | CoverEntityFeature.OPEN
        )
        if self._device.supports_position or self._device.supports_stop:
            # when stop is supported, xknx travelcalculator can set position
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION
        if self._device.step.writable:
            _supports_tilt = True
            self._attr_supported_features |= (
                CoverEntityFeature.CLOSE_TILT
                | CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.STOP_TILT
            )
        if self._device.supports_angle:
            _supports_tilt = True
            self._attr_supported_features |= CoverEntityFeature.SET_TILT_POSITION
        if self._device.supports_stop:
            self._attr_supported_features |= CoverEntityFeature.STOP
            if _supports_tilt:
                self._attr_supported_features |= CoverEntityFeature.STOP_TILT

        self._attr_device_class = CoverDeviceClass.BLIND if _supports_tilt else None