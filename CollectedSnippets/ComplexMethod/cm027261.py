def _async_update_zone_data(self) -> None:
        """Load tado data into zone."""
        self._tado_geofence_data = self._tado.data["geofence"]
        self._tado_zone_data = self._tado.data["zone"][self.zone_id]

        # Assign offset values to mapped attributes
        for offset_key, attr in TADO_TO_HA_OFFSET_MAP.items():
            if (
                self._device_id in self._tado.data["device"]
                and offset_key
                in self._tado.data["device"][self._device_id][TEMP_OFFSET]
            ):
                self._tado_zone_temp_offset[attr] = self._tado.data["device"][
                    self._device_id
                ][TEMP_OFFSET][offset_key]

        self._current_tado_hvac_mode = self._tado_zone_data.current_hvac_mode
        self._current_tado_hvac_action = self._tado_zone_data.current_hvac_action

        if self._is_valid_setting_for_hvac_mode(TADO_FANLEVEL_SETTING):
            self._current_tado_fan_level = self._tado_zone_data.current_fan_level
        if self._is_valid_setting_for_hvac_mode(TADO_FANSPEED_SETTING):
            self._current_tado_fan_speed = self._tado_zone_data.current_fan_speed
        if self._is_valid_setting_for_hvac_mode(TADO_SWING_SETTING):
            self._current_tado_swing_mode = self._tado_zone_data.current_swing_mode
        if self._is_valid_setting_for_hvac_mode(TADO_VERTICAL_SWING_SETTING):
            self._current_tado_vertical_swing = (
                self._tado_zone_data.current_vertical_swing_mode
            )
        if self._is_valid_setting_for_hvac_mode(TADO_HORIZONTAL_SWING_SETTING):
            self._current_tado_horizontal_swing = (
                self._tado_zone_data.current_horizontal_swing_mode
            )