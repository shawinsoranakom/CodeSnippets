def native_value(self) -> float | int | str | None:
        """Get the state of the ISY sensor device."""
        if self.target is None:
            return None

        if (value := self.target_value) == ISY_VALUE_UNKNOWN:
            return None

        # Get the translated ISY Unit of Measurement
        uom = self.raw_unit_of_measurement

        # Check if this is a known index pair UOM
        if isinstance(uom, dict):
            return uom.get(value, value)  # type: ignore[no-any-return]

        if uom in (UOM_INDEX, UOM_ON_OFF):
            return cast(str, self.target.formatted)

        # Check if this is an index type and get formatted value
        if uom == UOM_INDEX and hasattr(self.target, "formatted"):
            return cast(str, self.target.formatted)

        # Handle ISY precision and rounding
        value = convert_isy_value_to_hass(value, uom, self.target.prec)
        if value is None:
            return None

        # Convert temperatures to Home Assistant's unit
        if uom in (UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT):
            value = self.hass.config.units.temperature(value, uom)

        assert isinstance(value, (int, float))
        return value