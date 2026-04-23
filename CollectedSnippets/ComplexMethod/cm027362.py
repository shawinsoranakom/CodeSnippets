def _get_adjusted_display_precision(self) -> int | None:
        """Return the display precision for the sensor.

        When the integration has specified a suggested display precision, it will be used.
        If a unit conversion is needed, the display precision will be adjusted based on
        the ratio from the native unit to the current one.

        When the integration does not specify a suggested display precision, a default
        device class precision will be used from UNITS_PRECISION, and the final precision
        will be adjusted based on the ratio from the default unit to the current one. It
        will also be capped so that the extra precision (from the base unit) does not
        exceed DEFAULT_PRECISION_LIMIT.
        """
        display_precision = self.suggested_display_precision
        device_class = self.device_class
        if device_class is None:
            return display_precision

        default_unit_of_measurement = (
            self.suggested_unit_of_measurement
            or self.__native_unit_of_measurement_compat
        )
        if default_unit_of_measurement is None:
            return display_precision

        unit_of_measurement = self.unit_of_measurement
        if unit_of_measurement is None:
            return display_precision

        if display_precision is not None:
            if default_unit_of_measurement != unit_of_measurement:
                return (
                    _calculate_precision_from_ratio(
                        device_class,
                        default_unit_of_measurement,
                        unit_of_measurement,
                        display_precision,
                    )
                    or display_precision
                )
            return display_precision

        # Get the base unit and precision for the device class so we can use it to infer
        # the display precision for the current unit
        if device_class not in UNITS_PRECISION:
            return None
        device_class_base_unit, device_class_base_precision = UNITS_PRECISION[
            device_class
        ]

        precision = (
            _calculate_precision_from_ratio(
                device_class,
                device_class_base_unit,
                unit_of_measurement,
                device_class_base_precision,
            )
            if device_class_base_unit != unit_of_measurement
            else device_class_base_precision
        )
        if precision is None:
            return None

        # Since we are inferring the precision from the device class, cap it to avoid
        # having too many decimals
        return min(precision, device_class_base_precision + DEFAULT_PRECISION_LIMIT)