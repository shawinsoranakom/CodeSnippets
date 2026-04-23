def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target operation mode."""
        if not self._op_mode_device:
            return

        device = self._op_mode_device
        if "setOperatingMode" in device.actions:
            device.execute_action("setOperatingMode", [HA_OPMODES_HVAC[hvac_mode]])
        elif "setThermostatMode" in device.actions:
            if device.has_supported_thermostat_modes:
                for mode in device.supported_thermostat_modes:
                    if mode.lower() == hvac_mode:
                        device.execute_action("setThermostatMode", [mode])
                        break
        elif "setMode" in device.actions:
            device.execute_action("setMode", [HA_OPMODES_HVAC[hvac_mode]])