def __init__(self, client: Airtouch5SimpleClient, ability: AcAbility) -> None:
        """Initialise the Climate Entity."""
        super().__init__(client)
        self._ability = ability
        self._attr_unique_id = f"ac_{ability.ac_number}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"ac_{ability.ac_number}")},
            name=f"AC {ability.ac_number}",
            manufacturer="Polyaire",
            model="AirTouch 5",
        )
        self._attr_hvac_modes = [HVACMode.OFF]
        if ability.supports_mode_auto:
            self._attr_hvac_modes.append(HVACMode.AUTO)
        if ability.supports_mode_cool:
            self._attr_hvac_modes.append(HVACMode.COOL)
        if ability.supports_mode_dry:
            self._attr_hvac_modes.append(HVACMode.DRY)
        if ability.supports_mode_fan:
            self._attr_hvac_modes.append(HVACMode.FAN_ONLY)
        if ability.supports_mode_heat:
            self._attr_hvac_modes.append(HVACMode.HEAT)

        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        )
        if len(self.hvac_modes) > 1:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )

        self._attr_fan_modes = []
        if ability.supports_fan_speed_quiet:
            self._attr_fan_modes.append(FAN_DIFFUSE)
        if ability.supports_fan_speed_low:
            self._attr_fan_modes.append(FAN_LOW)
        if ability.supports_fan_speed_medium:
            self._attr_fan_modes.append(FAN_MEDIUM)
        if ability.supports_fan_speed_high:
            self._attr_fan_modes.append(FAN_HIGH)
        if ability.supports_fan_speed_powerful:
            self._attr_fan_modes.append(FAN_FOCUS)
        if ability.supports_fan_speed_turbo:
            self._attr_fan_modes.append(FAN_TURBO)
        if ability.supports_fan_speed_auto:
            self._attr_fan_modes.append(FAN_AUTO)
        if ability.supports_fan_speed_intelligent_auto:
            self._attr_fan_modes.append(FAN_INTELLIGENT_AUTO)

        # We can have different setpoints for heat cool, we expose the lowest low and highest high
        self._attr_min_temp = min(
            ability.min_cool_set_point, ability.min_heat_set_point
        )
        self._attr_max_temp = max(
            ability.max_cool_set_point, ability.max_heat_set_point
        )