def native_value(self) -> str | int | float | None:
        """Return the state."""
        state = self._state
        desc = self.entity_description

        if state is None:
            return state

        if desc.value_map is not None:
            return desc.value_map(state).name.lower()

        if desc.multiplication_factor is not None:
            state = handle_conversion(state, desc.multiplication_factor)

        # If there is an imperial conversion needed and the instance is using imperial,
        # apply the conversion logic.
        if (
            desc.imperial_conversion
            and desc.unit_imperial is not None
            and desc.unit_imperial != desc.unit_metric
            and self.hass.config.units is US_CUSTOMARY_SYSTEM
        ):
            return handle_conversion(state, desc.imperial_conversion)

        return state