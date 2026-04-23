def set_preset_mode(self, preset_mode: str) -> None:
        """Activate a preset."""
        preset_mode = HASS_TO_ECOBEE_PRESET.get(preset_mode, preset_mode)

        if preset_mode == self.preset_mode:
            return

        self.update_without_throttle = True

        # If we are currently in vacation mode, cancel it.
        if self.preset_mode == PRESET_VACATION:
            self.data.ecobee.delete_vacation(self.thermostat_index, self.vacation)

        if preset_mode == PRESET_AWAY_INDEFINITELY:
            self.data.ecobee.set_climate_hold(
                self.thermostat_index, "away", "indefinite", self.hold_hours()
            )

        elif preset_mode == PRESET_TEMPERATURE:
            self.set_temp_hold(self.current_temperature)

        elif preset_mode in (PRESET_HOLD_NEXT_TRANSITION, PRESET_HOLD_INDEFINITE):
            self.data.ecobee.set_climate_hold(
                self.thermostat_index,
                PRESET_TO_ECOBEE_HOLD[preset_mode],
                self.hold_preference(),
                self.hold_hours(),
            )

        elif preset_mode == PRESET_NONE:
            self.data.ecobee.resume_program(self.thermostat_index)

        else:
            for climate_ref, name in self.comfort_settings.items():
                if name == preset_mode:
                    preset_mode = climate_ref
                    break
            else:
                _LOGGER.warning("Received unknown preset mode: %s", preset_mode)

            self.data.ecobee.set_climate_hold(
                self.thermostat_index,
                preset_mode,
                self.hold_preference(),
                self.hold_hours(),
            )