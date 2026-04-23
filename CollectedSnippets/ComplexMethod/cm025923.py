def __init__(
        self,
        device_serial: str | None,
        device_config: PyViCareDeviceConfig,
        device: PyViCareDevice,
    ) -> None:
        """Initialize the fan entity."""
        super().__init__(
            self._attr_translation_key, device_serial, device_config, device
        )
        # init preset_mode
        supported_modes = list[str](self._api.getVentilationModes())
        self._attr_preset_modes = [
            mode
            for mode in VentilationMode
            if VentilationMode.to_vicare_mode(mode) in supported_modes
        ]
        if len(self._attr_preset_modes) > 0:
            self._attr_supported_features |= FanEntityFeature.PRESET_MODE
        # init set_speed
        supported_levels: list[str] | None = None
        with suppress(PyViCareNotSupportedFeatureError):
            supported_levels = self._api.getVentilationLevels()
        if supported_levels is not None and len(supported_levels) > 0:
            self._attr_supported_features |= FanEntityFeature.SET_SPEED

        # evaluate quickmodes
        self._attributes["vicare_quickmodes"] = quickmodes = list[str](
            device.getVentilationQuickmodes()
            if is_supported(
                "getVentilationQuickmodes",
                lambda api: api.getVentilationQuickmodes(),
                device,
            )
            else []
        )
        if VentilationQuickmode.STANDBY in quickmodes:
            self._attr_supported_features |= FanEntityFeature.TURN_OFF