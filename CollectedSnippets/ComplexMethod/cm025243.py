def __init__(
        self,
        device: MiioDevice,
        entry: XiaomiMiioConfigEntry,
        unique_id: str | None,
        coordinator: DataUpdateCoordinator[Any],
    ) -> None:
        """Initialize the plug switch."""
        super().__init__(device, entry, unique_id, coordinator)

        if self._model == MODEL_AIRPURIFIER_PRO:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_PRO
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_PRO
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_PRO
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        elif self._model in [MODEL_AIRPURIFIER_4, MODEL_AIRPURIFIER_4_PRO]:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_4
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_MIOT
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_MIOT
            self._attr_supported_features = (
                FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
            )
            self._attr_speed_count = 3
        elif self._model in [
            MODEL_AIRPURIFIER_4_LITE_RMA1,
            MODEL_AIRPURIFIER_4_LITE_RMB1,
        ]:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_4_LITE
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_MIOT
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_4_LITE
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        elif self._model == MODEL_AIRPURIFIER_PRO_V7:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_PRO_V7
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_PRO_V7
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_PRO_V7
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        elif self._model in [MODEL_AIRPURIFIER_2S, MODEL_AIRPURIFIER_2H]:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_2S
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_COMMON
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_2S
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        elif self._model == MODEL_AIRPURIFIER_ZA1:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_ZA1
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_MIOT
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_ZA1
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        elif self._model in MODELS_PURIFIER_MIOT:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_MIOT
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_MIOT
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_MIOT
            self._attr_supported_features = (
                FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
            )
            self._attr_speed_count = 3
        elif self._model == MODEL_AIRPURIFIER_V3:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_V3
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_V3
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER_V3
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        else:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_MIIO
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER
            self._attr_preset_modes = PRESET_MODES_AIRPURIFIER
            self._attr_supported_features = FanEntityFeature.PRESET_MODE
            self._attr_speed_count = 1
        self._attr_supported_features |= (
            FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
        )

        self._attr_is_on = self.coordinator.data.is_on
        self._attr_extra_state_attributes.update(
            {
                key: self._extract_value_from_attribute(self.coordinator.data, value)
                for key, value in self._available_attributes.items()
            }
        )
        self._mode = self.coordinator.data.mode.value
        self._fan_level = getattr(self.coordinator.data, ATTR_FAN_LEVEL, None)