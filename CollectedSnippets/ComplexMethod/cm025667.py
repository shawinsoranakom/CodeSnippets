def native_value(self) -> float | datetime | None:
        """Return the state."""
        if (
            not (observation := self._nws.observation)
            or (value := observation.get(self.entity_description.key)) is None
        ):
            return None

        # Set alias to unit property -> prevent unnecessary hasattr calls
        unit_of_measurement = self.native_unit_of_measurement
        if unit_of_measurement == UnitOfSpeed.MILES_PER_HOUR:
            return round(
                SpeedConverter.convert(
                    value, UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfSpeed.MILES_PER_HOUR
                )
            )
        if unit_of_measurement == UnitOfLength.MILES:
            return round(
                DistanceConverter.convert(
                    value, UnitOfLength.METERS, UnitOfLength.MILES
                )
            )
        if unit_of_measurement == UnitOfPressure.INHG:
            return round(
                PressureConverter.convert(
                    value, UnitOfPressure.PA, UnitOfPressure.INHG
                ),
                2,
            )
        if unit_of_measurement == UnitOfTemperature.CELSIUS:
            return round(value, 1)
        if unit_of_measurement == PERCENTAGE:
            return round(value)
        if self.device_class == SensorDeviceClass.TIMESTAMP:
            return parse_datetime(value)
        return value