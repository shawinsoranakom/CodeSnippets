def _update_from_device(self) -> None:
        """Update from device."""
        self._calculate_features()

        if self.get_matter_attribute_value(clusters.OnOff.Attributes.OnOff) is False:
            # special case: the appliance has a dedicated Power switch on the OnOff cluster
            # if the mains power is off - treat it as if the fan mode is off
            self._attr_preset_mode = None
            self._attr_percentage = 0
            return

        if self._attr_supported_features & FanEntityFeature.DIRECTION:
            direction_value = self.get_matter_attribute_value(
                clusters.FanControl.Attributes.AirflowDirection
            )
            self._attr_current_direction = (
                DIRECTION_REVERSE
                if direction_value
                == clusters.FanControl.Enums.AirflowDirectionEnum.kReverse
                else DIRECTION_FORWARD
            )
        if self._attr_supported_features & FanEntityFeature.OSCILLATE:
            self._attr_oscillating = (
                self.get_matter_attribute_value(
                    clusters.FanControl.Attributes.RockSetting
                )
                != 0
            )

        # speed percentage is always provided
        current_percent = self.get_matter_attribute_value(
            clusters.FanControl.Attributes.PercentCurrent
        )
        # NOTE that a device may give back 255 as a special value to indicate that
        # the speed is under automatic control and not set to a specific value.
        self._attr_percentage = None if current_percent == 255 else current_percent

        # get preset mode from fan mode (and wind feature if available)
        wind_setting = self.get_matter_attribute_value(
            clusters.FanControl.Attributes.WindSetting
        )
        fan_mode = self.get_matter_attribute_value(
            clusters.FanControl.Attributes.FanMode
        )
        if fan_mode == clusters.FanControl.Enums.FanModeEnum.kOff:
            self._attr_preset_mode = None
            self._attr_percentage = 0
        elif (
            self._attr_preset_modes
            and PRESET_NATURAL_WIND in self._attr_preset_modes
            and wind_setting & WindBitmap.kNaturalWind
        ):
            self._attr_preset_mode = PRESET_NATURAL_WIND
        elif (
            self._attr_preset_modes
            and PRESET_SLEEP_WIND in self._attr_preset_modes
            and wind_setting & WindBitmap.kSleepWind
        ):
            self._attr_preset_mode = PRESET_SLEEP_WIND
        else:
            fan_mode = self.get_matter_attribute_value(
                clusters.FanControl.Attributes.FanMode
            )
            self._attr_preset_mode = FAN_MODE_MAP_REVERSE.get(fan_mode)

        # keep track of the last known mode for turn_on commands without preset
        if self._attr_preset_mode is not None:
            self._last_known_preset_mode = self._attr_preset_mode
        if current_percent:
            self._last_known_percentage = current_percent