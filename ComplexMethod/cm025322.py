def async_registry_entry_updated(self) -> None:
        """Run when the entity registry entry has been updated."""
        if TYPE_CHECKING:
            assert self.registry_entry
        if (
            (number_options := self.registry_entry.options.get(DOMAIN))
            and (custom_unit := number_options.get(CONF_UNIT_OF_MEASUREMENT))
            and (device_class := self.device_class) in UNIT_CONVERTERS
            and self.__native_unit_of_measurement_compat
            in UNIT_CONVERTERS[device_class].VALID_UNITS
            and custom_unit in UNIT_CONVERTERS[device_class].VALID_UNITS
        ):
            self._number_option_unit_of_measurement = custom_unit
            return

        self._number_option_unit_of_measurement = None