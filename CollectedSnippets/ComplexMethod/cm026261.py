def _on_static_info_update(self, static_info: EntityInfo) -> None:
        """Set attrs from static info."""
        super()._on_static_info_update(static_info)
        static_info = self._static_info
        self._feature_flags = ClimateFeature(
            static_info.supported_feature_flags_compat(self._api_version)
        )
        self._attr_precision = self._get_precision()
        self._attr_hvac_modes = [
            _CLIMATE_MODES.from_esphome(mode) for mode in static_info.supported_modes
        ]
        self._attr_fan_modes = [
            _FAN_MODES.from_esphome(mode) for mode in static_info.supported_fan_modes
        ] + static_info.supported_custom_fan_modes
        self._attr_preset_modes = [
            _PRESETS.from_esphome(preset)
            for preset in static_info.supported_presets_compat(self._api_version)
        ] + static_info.supported_custom_presets
        self._attr_swing_modes = [
            _SWING_MODES.from_esphome(mode)
            for mode in static_info.supported_swing_modes
        ]
        # Round to one digit because of floating point math
        self._attr_target_temperature_step = round(
            static_info.visual_target_temperature_step, 1
        )
        self._attr_min_temp = static_info.visual_min_temperature
        self._attr_max_temp = static_info.visual_max_temperature
        self._attr_min_humidity = round(static_info.visual_min_humidity)
        self._attr_max_humidity = round(static_info.visual_max_humidity)
        features = ClimateEntityFeature(0)
        if self._feature_flags & ClimateFeature.SUPPORTS_TARGET_HUMIDITY:
            features |= ClimateEntityFeature.TARGET_HUMIDITY
        if self._feature_flags & ClimateFeature.REQUIRES_TWO_POINT_TARGET_TEMPERATURE:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        else:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
            if (
                self._feature_flags
                & ClimateFeature.SUPPORTS_TWO_POINT_TARGET_TEMPERATURE
            ):
                features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        if self.preset_modes:
            features |= ClimateEntityFeature.PRESET_MODE
        if self.fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        if self.swing_modes:
            features |= ClimateEntityFeature.SWING_MODE
        if len(self.hvac_modes) > 1 and HVACMode.OFF in self.hvac_modes:
            features |= ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        self._attr_supported_features = features