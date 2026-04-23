def update_native_value(self) -> None:
        """Set the value of the entity."""
        self._attr_current_option = (
            self.entity_description.values_translation_key.get(
                cast(str, self.option_value), None
            )
            if self.option_value is not None
            else None
        )
        if (
            (option_definition := self.appliance.options.get(self.bsh_key))
            and (option_constraints := option_definition.constraints)
            and option_constraints.allowed_values
            and self._original_option_keys != set(option_constraints.allowed_values)
        ):
            self._original_option_keys = set(option_constraints.allowed_values)
            self._attr_options = [
                self.entity_description.values_translation_key[option]
                for option in self._original_option_keys
                if option is not None
                and option in self.entity_description.values_translation_key
            ]