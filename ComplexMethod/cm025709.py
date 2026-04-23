def _update_hvac_mode_and_action(self) -> None:
        """Update HVAC mode and action from device."""
        if self.get_matter_attribute_value(clusters.OnOff.Attributes.OnOff) is False:
            # special case: the appliance has a dedicated Power switch on the OnOff cluster
            # if the mains power is off - treat it as if the HVAC mode is off
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_hvac_action = None
        else:
            # update hvac_mode from SystemMode
            system_mode_value = int(
                self.get_matter_attribute_value(
                    clusters.Thermostat.Attributes.SystemMode
                )
            )
            match system_mode_value:
                case SystemModeEnum.kAuto:
                    self._attr_hvac_mode = HVACMode.HEAT_COOL
                case SystemModeEnum.kDry:
                    self._attr_hvac_mode = HVACMode.DRY
                case SystemModeEnum.kFanOnly:
                    self._attr_hvac_mode = HVACMode.FAN_ONLY
                case SystemModeEnum.kCool | SystemModeEnum.kPrecooling:
                    self._attr_hvac_mode = HVACMode.COOL
                case SystemModeEnum.kHeat | SystemModeEnum.kEmergencyHeat:
                    self._attr_hvac_mode = HVACMode.HEAT
                case SystemModeEnum.kFanOnly:
                    self._attr_hvac_mode = HVACMode.FAN_ONLY
                case SystemModeEnum.kDry:
                    self._attr_hvac_mode = HVACMode.DRY
                case _:
                    self._attr_hvac_mode = HVACMode.OFF
            # running state is an optional attribute
            # which we map to hvac_action if it exists (its value is not None)
            self._attr_hvac_action = None
            if running_state_value := self.get_matter_attribute_value(
                clusters.Thermostat.Attributes.ThermostatRunningState
            ):
                if running_state_value & (
                    ThermostatRunningState.Heat | ThermostatRunningState.HeatStage2
                ):
                    self._attr_hvac_action = HVACAction.HEATING
                elif running_state_value & (
                    ThermostatRunningState.Cool | ThermostatRunningState.CoolStage2
                ):
                    self._attr_hvac_action = HVACAction.COOLING
                elif running_state_value & (
                    ThermostatRunningState.Fan
                    | ThermostatRunningState.FanStage2
                    | ThermostatRunningState.FanStage3
                ):
                    self._attr_hvac_action = HVACAction.FAN
                else:
                    self._attr_hvac_action = HVACAction.OFF