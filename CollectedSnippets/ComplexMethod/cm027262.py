async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set swing modes for the device."""
        vertical_swing = None
        horizontal_swing = None
        swing = None
        if self._attr_swing_modes is None:
            return
        if swing_mode == SWING_OFF:
            if self._is_valid_setting_for_hvac_mode(TADO_SWING_SETTING):
                swing = TADO_SWING_OFF
            if self._is_valid_setting_for_hvac_mode(TADO_HORIZONTAL_SWING_SETTING):
                horizontal_swing = TADO_SWING_OFF
            if self._is_valid_setting_for_hvac_mode(TADO_VERTICAL_SWING_SETTING):
                vertical_swing = TADO_SWING_OFF
        if swing_mode == SWING_ON:
            swing = TADO_SWING_ON
        if swing_mode == SWING_VERTICAL:
            if self._is_valid_setting_for_hvac_mode(TADO_VERTICAL_SWING_SETTING):
                vertical_swing = TADO_SWING_ON
            if self._is_valid_setting_for_hvac_mode(TADO_HORIZONTAL_SWING_SETTING):
                horizontal_swing = TADO_SWING_OFF
        if swing_mode == SWING_HORIZONTAL:
            if self._is_valid_setting_for_hvac_mode(TADO_VERTICAL_SWING_SETTING):
                vertical_swing = TADO_SWING_OFF
            if self._is_valid_setting_for_hvac_mode(TADO_HORIZONTAL_SWING_SETTING):
                horizontal_swing = TADO_SWING_ON
        if swing_mode == SWING_BOTH:
            if self._is_valid_setting_for_hvac_mode(TADO_VERTICAL_SWING_SETTING):
                vertical_swing = TADO_SWING_ON
            if self._is_valid_setting_for_hvac_mode(TADO_HORIZONTAL_SWING_SETTING):
                horizontal_swing = TADO_SWING_ON

        await self._control_hvac(
            swing_mode=swing,
            vertical_swing=vertical_swing,
            horizontal_swing=horizontal_swing,
        )
        await self.coordinator.async_request_refresh()