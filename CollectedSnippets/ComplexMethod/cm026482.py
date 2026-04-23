def interfaces(self) -> Generator[AlexaCapability]:
        """Yield the supported interfaces."""
        # If we support two modes, one being off, we allow turning on too.
        supported_features = self.entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if (
            (
                self.entity.domain == climate.DOMAIN
                and climate.HVACMode.OFF
                in (self.entity.attributes.get(climate.ATTR_HVAC_MODES) or [])
            )
            or (
                self.entity.domain == climate.DOMAIN
                and (
                    supported_features
                    & (
                        climate.ClimateEntityFeature.TURN_ON
                        | climate.ClimateEntityFeature.TURN_OFF
                    )
                )
            )
            or (
                self.entity.domain == water_heater.DOMAIN
                and (supported_features & water_heater.WaterHeaterEntityFeature.ON_OFF)
            )
        ):
            yield AlexaPowerController(self.entity)

        if self.entity.domain == climate.DOMAIN or (
            self.entity.domain == water_heater.DOMAIN
            and (
                supported_features
                & water_heater.WaterHeaterEntityFeature.OPERATION_MODE
            )
        ):
            yield AlexaThermostatController(self.hass, self.entity)
            yield AlexaTemperatureSensor(self.hass, self.entity)
        if (
            self.entity.domain == water_heater.DOMAIN
            and (
                supported_features
                & water_heater.WaterHeaterEntityFeature.OPERATION_MODE
            )
            and self.entity.attributes.get(water_heater.ATTR_OPERATION_LIST)
        ):
            yield AlexaModeController(
                self.entity,
                instance=f"{water_heater.DOMAIN}.{water_heater.ATTR_OPERATION_MODE}",
            )
        yield AlexaEndpointHealth(self.hass, self.entity)
        yield Alexa(self.entity)