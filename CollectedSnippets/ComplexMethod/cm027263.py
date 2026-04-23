async def _control_hvac(
        self,
        hvac_mode: str | None = None,
        target_temp: float | None = None,
        fan_mode: str | None = None,
        swing_mode: str | None = None,
        duration: int | None = None,
        overlay_mode: str | None = None,
        vertical_swing: str | None = None,
        horizontal_swing: str | None = None,
    ):
        """Send new target temperature to Tado."""
        if hvac_mode:
            self._current_tado_hvac_mode = hvac_mode

        if target_temp:
            self._target_temp = target_temp

        if fan_mode:
            if self._is_valid_setting_for_hvac_mode(TADO_FANSPEED_SETTING):
                self._current_tado_fan_speed = fan_mode
            if self._is_valid_setting_for_hvac_mode(TADO_FANLEVEL_SETTING):
                self._current_tado_fan_level = fan_mode

        if swing_mode:
            self._current_tado_swing_mode = swing_mode

        if vertical_swing:
            self._current_tado_vertical_swing = vertical_swing

        if horizontal_swing:
            self._current_tado_horizontal_swing = horizontal_swing

        self._normalize_target_temp_for_hvac_mode()

        # tado does not permit setting the fan speed to
        # off, you must turn off the device
        if (
            self._current_tado_fan_speed == CONST_FAN_OFF
            and self._current_tado_hvac_mode != CONST_MODE_OFF
        ):
            self._current_tado_fan_speed = CONST_FAN_AUTO

        if self._current_tado_hvac_mode == CONST_MODE_OFF:
            _LOGGER.debug(
                "Switching to OFF for zone %s (%d)", self.zone_name, self.zone_id
            )
            await self._tado.set_zone_off(
                self.zone_id, CONST_OVERLAY_MANUAL, self.zone_type
            )
            return

        if self._current_tado_hvac_mode == CONST_MODE_SMART_SCHEDULE:
            _LOGGER.debug(
                "Switching to SMART_SCHEDULE for zone %s (%d)",
                self.zone_name,
                self.zone_id,
            )
            await self._tado.reset_zone_overlay(self.zone_id)
            return

        overlay_mode = decide_overlay_mode(
            coordinator=self._tado,
            duration=duration,
            overlay_mode=overlay_mode,
            zone_id=self.zone_id,
        )
        duration = decide_duration(
            coordinator=self._tado,
            duration=duration,
            zone_id=self.zone_id,
            overlay_mode=overlay_mode,
        )
        _LOGGER.debug(
            (
                "Switching to %s for zone %s (%d) with temperature %s °C and duration"
                " %s using overlay %s"
            ),
            self._current_tado_hvac_mode,
            self.zone_name,
            self.zone_id,
            self._target_temp,
            duration,
            overlay_mode,
        )

        temperature_to_send = self._target_temp
        if self._current_tado_hvac_mode in TADO_MODES_WITH_NO_TEMP_SETTING:
            # A temperature cannot be passed with these modes
            temperature_to_send = None

        fan_speed = None
        fan_level = None
        if self.supported_features & ClimateEntityFeature.FAN_MODE:
            if self._is_current_setting_supported_by_current_hvac_mode(
                TADO_FANSPEED_SETTING, self._current_tado_fan_speed
            ):
                fan_speed = self._current_tado_fan_speed
            if self._is_current_setting_supported_by_current_hvac_mode(
                TADO_FANLEVEL_SETTING, self._current_tado_fan_level
            ):
                fan_level = self._current_tado_fan_level

        swing = None
        vertical_swing = None
        horizontal_swing = None
        if (
            self.supported_features & ClimateEntityFeature.SWING_MODE
        ) and self._attr_swing_modes is not None:
            if self._is_current_setting_supported_by_current_hvac_mode(
                TADO_VERTICAL_SWING_SETTING, self._current_tado_vertical_swing
            ):
                vertical_swing = self._current_tado_vertical_swing
            if self._is_current_setting_supported_by_current_hvac_mode(
                TADO_HORIZONTAL_SWING_SETTING, self._current_tado_horizontal_swing
            ):
                horizontal_swing = self._current_tado_horizontal_swing
            if self._is_current_setting_supported_by_current_hvac_mode(
                TADO_SWING_SETTING, self._current_tado_swing_mode
            ):
                swing = self._current_tado_swing_mode

        await self._tado.set_zone_overlay(
            zone_id=self.zone_id,
            overlay_mode=overlay_mode,  # What to do when the period ends
            temperature=temperature_to_send,
            duration=duration,
            device_type=self.zone_type,
            mode=self._current_tado_hvac_mode,
            fan_speed=fan_speed,  # api defaults to not sending fanSpeed if None specified
            swing=swing,  # api defaults to not sending swing if None specified
            fan_level=fan_level,  # api defaults to not sending fanLevel if fanSpeend not None
            vertical_swing=vertical_swing,  # api defaults to not sending verticalSwing if swing not None
            horizontal_swing=horizontal_swing,  # api defaults to not sending horizontalSwing if swing not None
        )