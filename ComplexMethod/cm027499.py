def _set_attr(self) -> None:
        if self.coordinator_context in self.coordinator.data:
            self._attr_fan_mode = FUJI_TO_HA_FAN.get(self.device.fan_speed)
            self._attr_fan_modes = [
                FUJI_TO_HA_FAN[mode]
                for mode in self.device.supported_fan_speeds
                if mode in FUJI_TO_HA_FAN
            ]
            self._attr_hvac_mode = FUJI_TO_HA_HVAC.get(self.device.op_mode)
            self._attr_hvac_modes = [
                FUJI_TO_HA_HVAC[mode]
                for mode in self.device.supported_op_modes
                if mode in FUJI_TO_HA_HVAC
            ]
            self._attr_swing_mode = FUJI_TO_HA_SWING.get(self.device.swing_mode)
            self._attr_swing_modes = [
                FUJI_TO_HA_SWING[mode]
                for mode in self.device.supported_swing_modes
                if mode in FUJI_TO_HA_SWING
            ]
            self._attr_min_temp = self.device.temperature_range[0]
            self._attr_max_temp = self.device.temperature_range[1]
            self._attr_current_temperature = self.device.sensed_temp
            self._attr_target_temperature = self.device.set_temp