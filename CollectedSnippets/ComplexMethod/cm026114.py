def __init__(self, entity_data: EntityData, **kwargs: Any) -> None:
        """Initialize the ZHA thermostat entity."""
        super().__init__(entity_data, **kwargs)
        self._attr_hvac_modes = [
            ZHA_TO_HA_HVAC_MODE[mode] for mode in self.entity_data.entity.hvac_modes
        ]
        self._attr_hvac_mode = ZHA_TO_HA_HVAC_MODE.get(
            self.entity_data.entity.hvac_mode
        )
        self._attr_hvac_action = ZHA_TO_HA_HVAC_ACTION.get(
            self.entity_data.entity.hvac_action
        )

        features: ClimateEntityFeature = ClimateEntityFeature(0)
        zha_features: ZHAClimateEntityFeature = (
            self.entity_data.entity.supported_features
        )

        if ZHAClimateEntityFeature.TARGET_TEMPERATURE in zha_features:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if ZHAClimateEntityFeature.TARGET_TEMPERATURE_RANGE in zha_features:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        if ZHAClimateEntityFeature.TARGET_HUMIDITY in zha_features:
            features |= ClimateEntityFeature.TARGET_HUMIDITY
        if ZHAClimateEntityFeature.PRESET_MODE in zha_features:
            features |= ClimateEntityFeature.PRESET_MODE
        if ZHAClimateEntityFeature.FAN_MODE in zha_features:
            features |= ClimateEntityFeature.FAN_MODE
        if ZHAClimateEntityFeature.SWING_MODE in zha_features:
            features |= ClimateEntityFeature.SWING_MODE
        if ZHAClimateEntityFeature.TURN_OFF in zha_features:
            features |= ClimateEntityFeature.TURN_OFF
        if ZHAClimateEntityFeature.TURN_ON in zha_features:
            features |= ClimateEntityFeature.TURN_ON

        self._attr_supported_features = features