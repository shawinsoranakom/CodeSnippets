def __init__(self, device: _LightDeviceT, hub: DeconzHub) -> None:
        """Set up light."""
        super().__init__(device, hub)

        self.api: GroupHandler | LightHandler
        if isinstance(self._device, Light):
            self.api = self.hub.api.lights.lights
        elif isinstance(self._device, Group):
            self.api = self.hub.api.groups

        self._attr_supported_color_modes: set[ColorMode] = set()

        if device.color_temp is not None:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)

        if device.hue is not None and device.saturation is not None:
            self._attr_supported_color_modes.add(ColorMode.HS)

        if device.xy is not None:
            self._attr_supported_color_modes.add(ColorMode.XY)

        if not self._attr_supported_color_modes and device.brightness is not None:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

        if not self._attr_supported_color_modes:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

        if device.brightness is not None:
            self._attr_supported_features |= (
                LightEntityFeature.FLASH | LightEntityFeature.TRANSITION
            )

        if device.effect is not None:
            self._attr_supported_features |= LightEntityFeature.EFFECT
            self._attr_effect_list = [EFFECT_COLORLOOP]

            # For lights that report supported effects.
            if isinstance(device, Light):
                if device.supported_effects is not None:
                    self._attr_effect_list = [
                        EFFECT_TO_DECONZ[el]
                        for el in device.supported_effects
                        if el in EFFECT_TO_DECONZ
                    ]
                if device.model_id in ("HG06467", "TS0601"):
                    self._attr_effect_list = XMAS_LIGHT_EFFECTS