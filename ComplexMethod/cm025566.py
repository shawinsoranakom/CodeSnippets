def update_native_value(self) -> None:
        """Set the value of the entity."""
        self._attr_native_value = cast(float | None, self.option_value)
        option_definition = self.appliance.options.get(self.bsh_key)
        if option_definition:
            if option_definition.unit:
                candidate_unit = UNIT_MAP.get(
                    option_definition.unit, option_definition.unit
                )
                if (
                    not hasattr(self, "_attr_native_unit_of_measurement")
                    or candidate_unit != self._attr_native_unit_of_measurement
                ):
                    self._attr_native_unit_of_measurement = candidate_unit
            option_constraints = option_definition.constraints
            if option_constraints:
                if (
                    not hasattr(self, "_attr_native_min_value")
                    or self._attr_native_min_value != option_constraints.min
                ) and option_constraints.min:
                    self._attr_native_min_value = option_constraints.min
                if (
                    not hasattr(self, "_attr_native_max_value")
                    or self._attr_native_max_value != option_constraints.max
                ) and option_constraints.max:
                    self._attr_native_max_value = option_constraints.max
                if (
                    not hasattr(self, "_attr_native_step")
                    or self._attr_native_step != option_constraints.step_size
                ) and option_constraints.step_size:
                    self._attr_native_step = option_constraints.step_size