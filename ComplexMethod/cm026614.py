def _validate_device_class_unit(self) -> None:
        """Validate device class unit compatibility."""

        # Logic to ensure the set device class and API received Unit Of Measurement
        # match Home Assistants requirements.
        if (
            self.device_class is not None
            and not self.device_class.startswith(DOMAIN)
            and self.entity_description.native_unit_of_measurement is None
            # we do not need to check mappings if the API UOM is allowed
            and self.native_unit_of_measurement
            not in SENSOR_DEVICE_CLASS_UNITS[self.device_class]
        ):
            # We cannot have a device class, if the UOM isn't set or the
            # device class cannot be found in the validation mapping.
            if (
                self.native_unit_of_measurement is None
                or self.device_class not in DEVICE_CLASS_UNITS
            ):
                LOGGER.debug(
                    "Device class %s ignored for incompatible unit %s in sensor entity %s",
                    self.device_class,
                    self.native_unit_of_measurement,
                    self.unique_id,
                )
                self._attr_device_class = None
                self._attr_suggested_unit_of_measurement = None
                return

            uoms = DEVICE_CLASS_UNITS[self.device_class]
            uom = uoms.get(self.native_unit_of_measurement) or uoms.get(
                self.native_unit_of_measurement.lower()
            )

            # Unknown unit of measurement, device class should not be used.
            if uom is None:
                self._attr_device_class = None
                self._attr_suggested_unit_of_measurement = None
                return

            # Found unit of measurement, use the standardized Unit
            # Use the target conversion unit (if set)
            self._attr_native_unit_of_measurement = uom.unit