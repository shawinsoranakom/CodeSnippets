def update_preset_mode(self) -> None:
        """Set the preset mode value."""
        option_value = None
        option_key = OptionKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_FAN_SPEED_MODE
        if event := self.appliance.events.get(EventKey(option_key)):
            option_value = event.value
        self._attr_preset_mode = (
            FAN_SPEED_MODE_OPTIONS_INVERTED.get(cast(str, option_value))
            if option_value is not None
            else None
        )
        if (
            (
                option_definition := self.appliance.options.get(
                    OptionKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_FAN_SPEED_MODE
                )
            )
            and (option_constraints := option_definition.constraints)
            and option_constraints.allowed_values
            and (
                allowed_values_without_none := {
                    value
                    for value in option_constraints.allowed_values
                    if value is not None
                }
            )
            and self._original_speed_modes_keys != allowed_values_without_none
        ):
            self._original_speed_modes_keys = allowed_values_without_none
            self._attr_preset_modes = [
                key
                for key, value in FAN_SPEED_MODE_OPTIONS.items()
                if value in self._original_speed_modes_keys
            ]