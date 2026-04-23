def _calculate_features(
        self,
    ) -> None:
        """Calculate features for HA Thermostat platform from Matter FeatureMap."""
        feature_map = int(
            self.get_matter_attribute_value(clusters.Thermostat.Attributes.FeatureMap)
        )
        # NOTE: the featuremap can dynamically change, so we need to update the
        # supported features if the featuremap changes.
        # work out supported features and presets from matter featuremap
        if self._feature_map == feature_map:
            return
        self._feature_map = feature_map
        product_id = self._endpoint.node.device_info.productID
        vendor_id = self._endpoint.node.device_info.vendorID
        self._attr_hvac_modes: list[HVACMode] = [HVACMode.OFF]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF
        )
        if feature_map & ThermostatFeature.kPresets:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
        # determine supported hvac modes
        if feature_map & ThermostatFeature.kHeating:
            self._attr_hvac_modes.append(HVACMode.HEAT)
        if feature_map & ThermostatFeature.kCooling:
            self._attr_hvac_modes.append(HVACMode.COOL)
        if (vendor_id, product_id) in SUPPORT_DRY_MODE_DEVICES:
            self._attr_hvac_modes.append(HVACMode.DRY)
        if (vendor_id, product_id) in SUPPORT_FAN_MODE_DEVICES:
            self._attr_hvac_modes.append(HVACMode.FAN_ONLY)
        if feature_map & ThermostatFeature.kAutoMode:
            self._attr_hvac_modes.append(HVACMode.HEAT_COOL)
            # only enable temperature_range feature if the device actually supports that

            if (vendor_id, product_id) not in SINGLE_SETPOINT_DEVICES:
                self._attr_supported_features |= (
                    ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
                )
        if any(mode for mode in self.hvac_modes if mode != HVACMode.OFF):
            self._attr_supported_features |= ClimateEntityFeature.TURN_ON