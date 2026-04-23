def _update_state(self) -> None:
        """Update the sensor state based on source sensors."""
        if self._is_inverted:
            source_state = self.hass.states.get(self._source_sensors[0])
            if source_state is None or source_state.state in ("unknown", "unavailable"):
                self._attr_native_value = None
                return
            try:
                value = float(source_state.state)
            except ValueError:
                self._attr_native_value = None
                return

            self._attr_native_value = value * -1

        elif self._is_combined:
            discharge_state = self.hass.states.get(self._source_sensors[0])
            charge_state = self.hass.states.get(self._source_sensors[1])

            if (
                discharge_state is None
                or charge_state is None
                or discharge_state.state in ("unknown", "unavailable")
                or charge_state.state in ("unknown", "unavailable")
            ):
                self._attr_native_value = None
                return

            try:
                discharge = float(discharge_state.state)
                charge = float(charge_state.state)
            except ValueError:
                self._attr_native_value = None
                return

            # Get units from state attributes
            discharge_unit = discharge_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            charge_unit = charge_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

            # Convert to Watts if units are present
            if discharge_unit:
                discharge = unit_conversion.PowerConverter.convert(
                    discharge, discharge_unit, UnitOfPower.WATT
                )
            if charge_unit:
                charge = unit_conversion.PowerConverter.convert(
                    charge, charge_unit, UnitOfPower.WATT
                )

            self._attr_native_value = discharge - charge