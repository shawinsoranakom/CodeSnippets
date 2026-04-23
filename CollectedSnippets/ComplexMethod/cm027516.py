def __init__(
        self, client: SmartThings, device: FullDevice, component: str = MAIN
    ) -> None:
        """Initialize a SmartThingsLight."""
        super().__init__(
            client,
            device,
            {
                Capability.COLOR_CONTROL,
                Capability.COLOR_TEMPERATURE,
                Capability.SWITCH_LEVEL,
                Capability.SWITCH,
            },
            component=component,
        )
        color_modes = set()
        if self.supports_capability(Capability.COLOR_TEMPERATURE):
            color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_color_mode = ColorMode.COLOR_TEMP
        if self.supports_capability(Capability.COLOR_CONTROL):
            color_modes.add(ColorMode.HS)
            self._attr_color_mode = ColorMode.HS
        if not color_modes and self.supports_capability(Capability.SWITCH_LEVEL):
            color_modes.add(ColorMode.BRIGHTNESS)
        if not color_modes:
            color_modes.add(ColorMode.ONOFF)
        if len(color_modes) == 1:
            self._attr_color_mode = list(color_modes)[0]
        self._attr_supported_color_modes = color_modes
        features = LightEntityFeature(0)
        if self.supports_capability(Capability.SWITCH_LEVEL):
            features |= LightEntityFeature.TRANSITION
        self._attr_supported_features = features