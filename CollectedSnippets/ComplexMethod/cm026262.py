async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature (and operation mode if set)."""
        data: dict[str, Any] = {"key": self._key}
        if ATTR_HVAC_MODE in kwargs:
            data["mode"] = _CLIMATE_MODES.from_hass(
                cast(HVACMode, kwargs[ATTR_HVAC_MODE])
            )
        if ATTR_TEMPERATURE in kwargs:
            if not self._feature_flags & (
                ClimateFeature.REQUIRES_TWO_POINT_TARGET_TEMPERATURE
                | ClimateFeature.SUPPORTS_TWO_POINT_TARGET_TEMPERATURE
            ):
                data["target_temperature"] = kwargs[ATTR_TEMPERATURE]
            else:
                hvac_mode = kwargs.get(ATTR_HVAC_MODE) or self.hvac_mode
                if hvac_mode == HVACMode.HEAT:
                    data["target_temperature_low"] = kwargs[ATTR_TEMPERATURE]
                elif hvac_mode == HVACMode.COOL:
                    data["target_temperature_high"] = kwargs[ATTR_TEMPERATURE]
                else:
                    raise ServiceValidationError(
                        translation_domain=DOMAIN,
                        translation_key="action_call_failed",
                        translation_placeholders={
                            "call_name": "climate.set_temperature",
                            "device_name": self._static_info.name,
                            "error": (
                                f"Setting target_temperature is only supported in "
                                f"{HVACMode.HEAT} or {HVACMode.COOL} modes"
                            ),
                        },
                    )
        if ATTR_TARGET_TEMP_LOW in kwargs:
            data["target_temperature_low"] = kwargs[ATTR_TARGET_TEMP_LOW]
        if ATTR_TARGET_TEMP_HIGH in kwargs:
            data["target_temperature_high"] = kwargs[ATTR_TARGET_TEMP_HIGH]
        self._client.climate_command(**data, device_id=self._static_info.device_id)