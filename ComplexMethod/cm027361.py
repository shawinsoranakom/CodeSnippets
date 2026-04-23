def state(self) -> Any:
        """Return the state of the sensor and perform unit conversions, if needed."""
        native_unit_of_measurement = self.__native_unit_of_measurement_compat
        unit_of_measurement = self.unit_of_measurement
        value = self.native_value
        # For the sake of validation, we can ignore custom device classes
        # (customization and legacy style translations)
        device_class = try_parse_enum(SensorDeviceClass, self.device_class)
        state_class = self.state_class

        # Sensors with device classes indicating a non-numeric value
        # should not have a unit of measurement
        if device_class in NON_NUMERIC_DEVICE_CLASSES and unit_of_measurement:
            raise ValueError(
                f"Sensor {self.entity_id} has a unit of measurement and thus "
                "indicating it has a numeric value; however, it has the "
                f"non-numeric device class: {device_class}"
            )

        # Validate state class for sensors with a device class
        if (
            state_class
            and not self._invalid_state_class_reported
            and device_class
            and (classes := DEVICE_CLASS_STATE_CLASSES.get(device_class)) is not None
            and state_class not in classes
        ):
            self._invalid_state_class_reported = True
            report_issue = self._suggest_report_issue()

            # This should raise in Home Assistant Core 2023.6
            _LOGGER.warning(
                "Entity %s (%s) is using state class '%s' which "
                "is impossible considering device class ('%s') it is using; "
                "expected %s%s; "
                "Please update your configuration if your entity is manually "
                "configured, otherwise %s",
                self.entity_id,
                type(self),
                state_class,
                device_class,
                "None or one of " if classes else "None",
                ", ".join(f"'{value.value}'" for value in classes),
                report_issue,
            )

        # Checks below only apply if there is a value
        if value is None:
            return None

        # Received a datetime
        if device_class is SensorDeviceClass.TIMESTAMP:
            try:
                # We cast the value, to avoid using isinstance, but satisfy
                # typechecking. The errors are guarded in this try.
                value = cast(datetime, value)
                if value.tzinfo is None:
                    raise ValueError(
                        f"Invalid datetime: {self.entity_id} provides state '{value}', "
                        "which is missing timezone information"
                    )

                if value.tzinfo != UTC:
                    value = value.astimezone(UTC)

                return value.isoformat(timespec="seconds")
            except (AttributeError, OverflowError, TypeError) as err:
                raise ValueError(
                    f"Invalid datetime: {self.entity_id} has timestamp device class "
                    f"but provides state {value}:{type(value)} resulting in '{err}'"
                ) from err

        # Received a date value
        if device_class is SensorDeviceClass.DATE:
            try:
                # We cast the value, to avoid using isinstance, but satisfy
                # typechecking. The errors are guarded in this try.
                value = cast(date, value)
                return value.isoformat()
            except (AttributeError, TypeError) as err:
                raise ValueError(
                    f"Invalid date: {self.entity_id} has date device class "
                    f"but provides state {value}:{type(value)} resulting in '{err}'"
                ) from err

        # Enum checks
        if (
            options := self.options
        ) is not None or device_class is SensorDeviceClass.ENUM:
            if device_class is not SensorDeviceClass.ENUM:
                reason = "is missing the enum device class"
                if device_class is not None:
                    reason = f"has device class '{device_class}' instead of 'enum'"
                raise ValueError(
                    f"Sensor {self.entity_id} is providing enum options, but {reason}"
                )

            if options and value not in options:
                raise ValueError(
                    f"Sensor {self.entity_id} provides state value '{value}', "
                    "which is not in the list of options provided"
                )
            return value

        suggested_precision = self.suggested_display_precision

        # If the sensor has neither a device class, a state class, a unit of measurement
        # nor a precision then there are no further checks or conversions
        if not _numeric_state_expected(
            device_class, state_class, native_unit_of_measurement, suggested_precision
        ):
            return value

        # From here on a numerical value is expected
        numerical_value: int | float | Decimal
        if not isinstance(value, (int, float, Decimal)):
            try:
                if isinstance(value, str) and "." not in value and "e" not in value:
                    try:
                        numerical_value = int(value)
                    except ValueError:
                        # Handle nan, inf
                        numerical_value = float(value)
                else:
                    numerical_value = float(value)  # type:ignore[arg-type]
            except (TypeError, ValueError) as err:
                raise ValueError(
                    f"Sensor {self.entity_id} has device class '{device_class}', "
                    f"state class '{state_class}' unit '{unit_of_measurement}' and "
                    f"suggested precision '{suggested_precision}' thus indicating it "
                    f"has a numeric value; however, it has the non-numeric value: "
                    f"'{value}' ({type(value)})"
                ) from err
        else:
            numerical_value = value

        if not isfinite(numerical_value):
            raise ValueError(
                f"Sensor {self.entity_id} has device class '{device_class}', "
                f"state class '{state_class}' unit '{unit_of_measurement}' and "
                f"suggested precision '{suggested_precision}' thus indicating it "
                f"has a numeric value; however, it has the non-finite value: "
                f"'{numerical_value}'"
            )

        if native_unit_of_measurement != unit_of_measurement and (
            converter := UNIT_CONVERTERS.get(device_class)
        ):
            # Unit conversion needed
            value = converter.converter_factory(
                native_unit_of_measurement, unit_of_measurement
            )(float(numerical_value))

        # Validate unit of measurement used for sensors with a device class
        if (
            not self._invalid_unit_of_measurement_reported
            and device_class
            and (units := DEVICE_CLASS_UNITS.get(device_class)) is not None
            and native_unit_of_measurement not in units
        ):
            self._invalid_unit_of_measurement_reported = True
            report_issue = self._suggest_report_issue()

            # This should raise in Home Assistant Core 2023.6
            _LOGGER.warning(
                (
                    "Entity %s (%s) is using native unit of measurement '%s' which "
                    "is not a valid unit for the device class ('%s') it is using; "
                    "expected one of %s; "
                    "Please update your configuration if your entity is manually "
                    "configured, otherwise %s"
                ),
                self.entity_id,
                type(self),
                native_unit_of_measurement,
                device_class,
                [str(unit) if unit else "no unit of measurement" for unit in units],
                report_issue,
            )

        # Validate unit of measurement used for sensors with a state class
        if (
            state_class
            and (units := STATE_CLASS_UNITS.get(state_class)) is not None
            and native_unit_of_measurement not in units
        ):
            raise ValueError(
                f"Sensor {self.entity_id} ({type(self)}) is using native unit of "
                f"measurement '{native_unit_of_measurement}' which is not a valid unit "
                f"for the state class ('{state_class}') it is using; expected one of {units};"
            )

        return value