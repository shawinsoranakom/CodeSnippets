def __init__(
        self,
        coordinator: GoveeLocalApiCoordinator,
        device: GoveeDevice,
    ) -> None:
        """Govee Light constructor."""

        super().__init__(coordinator)
        self._device = device

        self._attr_unique_id = device.fingerprint

        capabilities = device.capabilities
        color_modes = {ColorMode.ONOFF}
        if capabilities:
            if GoveeLightFeatures.COLOR_RGB & capabilities.features:
                color_modes.add(ColorMode.RGB)
            if GoveeLightFeatures.COLOR_KELVIN_TEMPERATURE & capabilities.features:
                color_modes.add(ColorMode.COLOR_TEMP)
                self._attr_max_color_temp_kelvin = 9000
                self._attr_min_color_temp_kelvin = 2000
            if GoveeLightFeatures.BRIGHTNESS & capabilities.features:
                color_modes.add(ColorMode.BRIGHTNESS)

            if (
                GoveeLightFeatures.SCENES & capabilities.features
                and capabilities.scenes
            ):
                self._attr_supported_features = LightEntityFeature.EFFECT
                self._attr_effect_list = [_NONE_SCENE, *capabilities.scenes.keys()]

        self._attr_supported_color_modes = filter_supported_color_modes(color_modes)
        if len(self._attr_supported_color_modes) == 1:
            # If the light supports only a single color mode, set it now
            self._fixed_color_mode = next(iter(self._attr_supported_color_modes))

        self._attr_device_info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, device.fingerprint)
            },
            name=device.sku,
            manufacturer=MANUFACTURER,
            model_id=device.sku,
            serial_number=device.fingerprint,
        )