def __init__(self, data: BondData, device: BondDevice) -> None:
        """Create HA entity representing Bond cover."""
        super().__init__(data, device)
        supported_features = CoverEntityFeature(0)
        if self._device.supports_set_position():
            supported_features |= CoverEntityFeature.SET_POSITION
        if self._device.supports_open():
            supported_features |= CoverEntityFeature.OPEN
        if self._device.supports_close():
            supported_features |= CoverEntityFeature.CLOSE
        if self._device.supports_tilt_open():
            supported_features |= CoverEntityFeature.OPEN_TILT
        if self._device.supports_tilt_close():
            supported_features |= CoverEntityFeature.CLOSE_TILT
        if self._device.supports_hold():
            if self._device.supports_open() or self._device.supports_close():
                supported_features |= CoverEntityFeature.STOP
            if self._device.supports_tilt_open() or self._device.supports_tilt_close():
                supported_features |= CoverEntityFeature.STOP_TILT
        self._attr_supported_features = supported_features