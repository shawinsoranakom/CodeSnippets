def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the entity, after unit conversion."""
        # Highest priority, for registered entities: unit set by user,with fallback to
        # unit suggested by integration or secondary fallback to unit conversion rules
        if self._sensor_option_unit_of_measurement is not UNDEFINED:
            return self._sensor_option_unit_of_measurement

        native_unit_of_measurement = self.__native_unit_of_measurement_compat

        # Second priority, for non registered entities: unit suggested by integration
        if not self.registry_entry and (
            suggested_unit_of_measurement := self.suggested_unit_of_measurement
        ):
            if self._is_valid_suggested_unit(suggested_unit_of_measurement):
                return suggested_unit_of_measurement

        # Third priority: Legacy temperature conversion, which applies
        # to both registered and non registered entities
        if (
            native_unit_of_measurement in TEMPERATURE_UNITS
            and self.device_class is SensorDeviceClass.TEMPERATURE
        ):
            return self.hass.config.units.temperature_unit

        # Fourth priority: Unit translation
        if (translation_key := self._unit_of_measurement_translation_key) and (
            unit_of_measurement
            := self.platform_data.default_language_platform_translations.get(
                translation_key
            )
        ):
            if native_unit_of_measurement is not None:
                raise ValueError(
                    f"Sensor {type(self)} from integration '{self.platform.platform_name}' "
                    f"has a translation key for unit_of_measurement '{unit_of_measurement}', "
                    f"but also has a native_unit_of_measurement '{native_unit_of_measurement}'"
                )
            return unit_of_measurement

        # Lowest priority: Native unit
        return native_unit_of_measurement