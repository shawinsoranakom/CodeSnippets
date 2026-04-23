def __init__(
        self,
        data: HoneywellData,
        device: SomeComfortDevice,
        cool_away_temp: int | None,
        heat_away_temp: int | None,
    ) -> None:
        """Initialize the thermostat."""
        self._data = data
        self._device = device
        self._cool_away_temp = cool_away_temp
        self._heat_away_temp = heat_away_temp
        self._away = False
        self._away_hold = False
        self._retry = 0

        self._attr_unique_id = str(device.deviceid)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.deviceid)},
            name=device.name,
            manufacturer="Honeywell",
        )

        self._attr_translation_placeholders = {"name": device.name}
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        if device.temperature_unit == "C":
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_preset_modes = [PRESET_NONE, PRESET_AWAY, PRESET_HOLD]

        # not all honeywell HVACs support all modes

        self._hvac_mode_map = {
            key2: value2
            for key1, value1 in HVAC_MODE_TO_HW_MODE.items()
            if device.raw_ui_data[key1]
            for key2, value2 in value1.items()
        }
        self._attr_hvac_modes = list(self._hvac_mode_map)

        self._attr_supported_features = (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )
        if len(self.hvac_modes) > 1 and HVACMode.OFF in self.hvac_modes:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )

        if device._data.get("canControlHumidification"):  # noqa: SLF001
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY

        if not device._data.get("hasFan"):  # noqa: SLF001
            return

        # not all honeywell fans support all modes
        self._fan_mode_map = {
            key2: value2
            for key1, value1 in FAN_MODE_TO_HW.items()
            if device.raw_fan_data[key1]
            for key2, value2 in value1.items()
        }

        self._attr_fan_modes = list(self._fan_mode_map)

        self._attr_supported_features |= ClimateEntityFeature.FAN_MODE