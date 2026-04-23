def _calculate_features(
        self,
    ) -> None:
        """Calculate features for HA Fan platform from Matter FeatureMap."""
        feature_map = int(
            self.get_matter_attribute_value(clusters.FanControl.Attributes.FeatureMap)
        )
        # NOTE: the featuremap can dynamically change, so we need to update the
        # supported features if the featuremap changes.
        # work out supported features and presets from matter featuremap
        if self._feature_map == feature_map:
            return
        self._feature_map = feature_map
        self._attr_supported_features = FanEntityFeature(0)
        if feature_map & FanControlFeature.kMultiSpeed:
            self._attr_supported_features |= FanEntityFeature.SET_SPEED
            self._attr_speed_count = int(
                self.get_matter_attribute_value(clusters.FanControl.Attributes.SpeedMax)
            )
        if feature_map & FanControlFeature.kRocking:
            # NOTE: the Matter model allows that a device can have multiple/different
            # rock directions while HA doesn't allow this in the entity model.
            # For now we just assume that a device has a single rock direction and the
            # Matter spec is just future proofing for devices that might have multiple
            # rock directions. As soon as devices show up that actually support multiple
            # directions, we need to either update the HA Fan entity model or maybe add
            # this as a separate entity.
            self._attr_supported_features |= FanEntityFeature.OSCILLATE

        # figure out supported preset modes
        preset_modes = []
        fan_mode_seq = int(
            self.get_matter_attribute_value(
                clusters.FanControl.Attributes.FanModeSequence
            )
        )
        if fan_mode_seq == FanModeSequenceEnum.kOffLowHigh:
            preset_modes = [PRESET_LOW, PRESET_HIGH]
        elif fan_mode_seq == FanModeSequenceEnum.kOffLowHighAuto:
            preset_modes = [PRESET_LOW, PRESET_HIGH, PRESET_AUTO]
        elif fan_mode_seq == FanModeSequenceEnum.kOffLowMedHigh:
            preset_modes = [PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH]
        elif fan_mode_seq == FanModeSequenceEnum.kOffLowMedHighAuto:
            preset_modes = [PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH, PRESET_AUTO]
        elif fan_mode_seq == FanModeSequenceEnum.kOffHighAuto:
            preset_modes = [PRESET_HIGH, PRESET_AUTO]
        elif fan_mode_seq == FanModeSequenceEnum.kOffHigh:
            preset_modes = [PRESET_HIGH]
        # treat Matter Wind feature as additional preset(s)
        if feature_map & FanControlFeature.kWind:
            wind_support = int(
                self.get_matter_attribute_value(
                    clusters.FanControl.Attributes.WindSupport
                )
            )
            if wind_support & WindBitmap.kNaturalWind:
                preset_modes.append(PRESET_NATURAL_WIND)
            if wind_support & WindBitmap.kSleepWind:
                preset_modes.append(PRESET_SLEEP_WIND)
        if len(preset_modes) > 0:
            self._attr_supported_features |= FanEntityFeature.PRESET_MODE
        self._attr_preset_modes = preset_modes
        if feature_map & FanControlFeature.kAirflowDirection:
            self._attr_supported_features |= FanEntityFeature.DIRECTION

        self._attr_supported_features |= (
            FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
        )