def _converter_factory(
        cls, from_unit: str | None, to_unit: str | None
    ) -> Callable[[float], float]:
        """Convert a temperature from one unit to another.

        eg. 10°C will return 50°F

        For converting an interval between two temperatures, please use
        `convert_interval` instead.
        """
        # We cannot use the implementation from BaseUnitConverter here because the
        # temperature units do not use the same floor: 0°C, 0°F and 0K do not align
        if from_unit == UnitOfTemperature.CELSIUS:
            if to_unit == UnitOfTemperature.FAHRENHEIT:
                return cls._celsius_to_fahrenheit
            if to_unit == UnitOfTemperature.KELVIN:
                return cls._celsius_to_kelvin
            raise HomeAssistantError(
                UNIT_NOT_RECOGNIZED_TEMPLATE.format(to_unit, cls.UNIT_CLASS)
            )

        if from_unit == UnitOfTemperature.FAHRENHEIT:
            if to_unit == UnitOfTemperature.CELSIUS:
                return cls._fahrenheit_to_celsius
            if to_unit == UnitOfTemperature.KELVIN:
                return cls._fahrenheit_to_kelvin
            raise HomeAssistantError(
                UNIT_NOT_RECOGNIZED_TEMPLATE.format(to_unit, cls.UNIT_CLASS)
            )

        if from_unit == UnitOfTemperature.KELVIN:
            if to_unit == UnitOfTemperature.CELSIUS:
                return cls._kelvin_to_celsius
            if to_unit == UnitOfTemperature.FAHRENHEIT:
                return cls._kelvin_to_fahrenheit
            raise HomeAssistantError(
                UNIT_NOT_RECOGNIZED_TEMPLATE.format(to_unit, cls.UNIT_CLASS)
            )
        raise HomeAssistantError(
            UNIT_NOT_RECOGNIZED_TEMPLATE.format(from_unit, cls.UNIT_CLASS)
        )