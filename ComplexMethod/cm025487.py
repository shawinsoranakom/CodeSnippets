def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if (
            not (default_unit := self.entity_description.native_unit_of_measurement)
            or not (state := self.device.states.get(self.entity_description.key))
            or not state.value
        ):
            return default_unit

        attrs = self.device.attributes
        if (unit := attrs[f"{state.name}MeasuredValueType"]) and (
            unit_value := unit.value_as_str
        ):
            return OVERKIZ_UNIT_TO_HA.get(unit_value, default_unit)

        if (unit := attrs[OverkizAttribute.CORE_MEASURED_VALUE_TYPE]) and (
            unit_value := unit.value_as_str
        ):
            return OVERKIZ_UNIT_TO_HA.get(unit_value, default_unit)

        return default_unit