def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool, dry, off mode."""

        if self.is_using_derogated_temperature_fallback:
            return super().hvac_mode

        if (device_hvac_mode := self.device_hvac_mode) is None:
            return HVACMode.OFF

        cooling_is_off = cast(
            str,
            self.executor.select_state(OverkizState.CORE_COOLING_ON_OFF),
        ) in (OverkizCommandParam.OFF, None)

        heating_is_off = cast(
            str,
            self.executor.select_state(OverkizState.CORE_HEATING_ON_OFF),
        ) in (OverkizCommandParam.OFF, None)

        # Device is Stopped, it means the air flux is flowing but its venting door is closed.
        if (
            (device_hvac_mode == HVACMode.COOL and cooling_is_off)
            or (device_hvac_mode == HVACMode.HEAT and heating_is_off)
            or (
                device_hvac_mode == HVACMode.HEAT_COOL
                and cooling_is_off
                and heating_is_off
            )
        ):
            return HVACMode.OFF

        return device_hvac_mode