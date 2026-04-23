def __init__(
        self,
        coordinator: ShellyBlockCoordinator,
        block: Block,
        attribute: str,
        description: BlockLightDescription,
    ) -> None:
        """Initialize block light."""
        super().__init__(coordinator, block, attribute, description)
        self.control_result: dict[str, Any] | None = None
        self._attr_name = None  # Main device entity
        self._attr_unique_id: str = f"{coordinator.mac}-{block.description}"
        self._attr_supported_color_modes = set()
        self._attr_min_color_temp_kelvin = KELVIN_MIN_VALUE_WHITE
        self._attr_max_color_temp_kelvin = KELVIN_MAX_VALUE

        if hasattr(block, "red") and hasattr(block, "green") and hasattr(block, "blue"):
            self._attr_min_color_temp_kelvin = KELVIN_MIN_VALUE_COLOR
            if coordinator.model in RGBW_MODELS:
                self._attr_supported_color_modes.add(ColorMode.RGBW)
            else:
                self._attr_supported_color_modes.add(ColorMode.RGB)

        if hasattr(block, "colorTemp"):
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)

        if not self._attr_supported_color_modes:
            if hasattr(block, "brightness") or hasattr(block, "gain"):
                self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
            else:
                self._attr_supported_color_modes.add(ColorMode.ONOFF)

        if hasattr(block, "effect"):
            self._attr_supported_features |= LightEntityFeature.EFFECT

        if coordinator.model in MODELS_SUPPORTING_LIGHT_TRANSITION:
            self._attr_supported_features |= LightEntityFeature.TRANSITION