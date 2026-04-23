def __init__(self, *args: Any) -> None:
        """Initialize a Thermostat accessory object."""
        super().__init__(*args, category=CATEGORY_THERMOSTAT)
        self._unit = self.hass.config.units.temperature_unit
        state = self.hass.states.get(self.entity_id)
        assert state
        hc_min_temp, hc_max_temp = self.get_temperature_range(state)
        self._reload_on_change_attrs.extend(
            (
                ATTR_MIN_HUMIDITY,
                ATTR_MAX_TEMP,
                ATTR_MIN_TEMP,
                ATTR_FAN_MODES,
                ATTR_HVAC_MODES,
            )
        )

        # Add additional characteristics if auto mode is supported
        self.chars: list[str] = []
        self.fan_chars: list[str] = []

        attributes = state.attributes
        min_humidity, _ = get_min_max(
            attributes.get(ATTR_MIN_HUMIDITY, DEFAULT_MIN_HUMIDITY),
            attributes.get(ATTR_MAX_HUMIDITY, DEFAULT_MAX_HUMIDITY),
        )
        features = attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        if features & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE:
            self.chars.extend(
                (CHAR_COOLING_THRESHOLD_TEMPERATURE, CHAR_HEATING_THRESHOLD_TEMPERATURE)
            )

        if (
            ATTR_CURRENT_HUMIDITY in attributes
            or features & ClimateEntityFeature.TARGET_HUMIDITY
        ):
            self.chars.append(CHAR_CURRENT_HUMIDITY)

        if features & ClimateEntityFeature.TARGET_HUMIDITY:
            self.chars.append(CHAR_TARGET_HUMIDITY)

        serv_thermostat = self.add_preload_service(SERV_THERMOSTAT, self.chars)
        self.set_primary_service(serv_thermostat)

        # Current mode characteristics
        self.char_current_heat_cool = serv_thermostat.configure_char(
            CHAR_CURRENT_HEATING_COOLING, value=0
        )

        self._configure_hvac_modes(state)
        # Must set the value first as setting
        # valid_values happens before setting
        # the value and if 0 is not a valid
        # value this will throw
        self.char_target_heat_cool = serv_thermostat.configure_char(
            CHAR_TARGET_HEATING_COOLING, value=list(self.hc_homekit_to_hass)[0]
        )
        self.char_target_heat_cool.override_properties(
            valid_values=self.hc_hass_to_homekit
        )
        self.char_target_heat_cool.allow_invalid_client_values = True
        # Current and target temperature characteristics

        self.char_current_temp = serv_thermostat.configure_char(
            CHAR_CURRENT_TEMPERATURE, value=21.0
        )

        self.char_target_temp = serv_thermostat.configure_char(
            CHAR_TARGET_TEMPERATURE,
            value=21.0,
            # We do not set PROP_MIN_STEP here and instead use the HomeKit
            # default of 0.1 in order to have enough precision to convert
            # temperature units and avoid setting to 73F will result in 74F
            properties={PROP_MIN_VALUE: hc_min_temp, PROP_MAX_VALUE: hc_max_temp},
        )

        # Display units characteristic
        self.char_display_units = serv_thermostat.configure_char(
            CHAR_TEMP_DISPLAY_UNITS, value=0
        )

        # If the device supports it: high and low temperature characteristics
        self.char_cooling_thresh_temp = None
        self.char_heating_thresh_temp = None
        if CHAR_COOLING_THRESHOLD_TEMPERATURE in self.chars:
            self.char_cooling_thresh_temp = serv_thermostat.configure_char(
                CHAR_COOLING_THRESHOLD_TEMPERATURE,
                value=23.0,
                # We do not set PROP_MIN_STEP here and instead use the HomeKit
                # default of 0.1 in order to have enough precision to convert
                # temperature units and avoid setting to 73F will result in 74F
                properties={PROP_MIN_VALUE: hc_min_temp, PROP_MAX_VALUE: hc_max_temp},
            )
        if CHAR_HEATING_THRESHOLD_TEMPERATURE in self.chars:
            self.char_heating_thresh_temp = serv_thermostat.configure_char(
                CHAR_HEATING_THRESHOLD_TEMPERATURE,
                value=19.0,
                # We do not set PROP_MIN_STEP here and instead use the HomeKit
                # default of 0.1 in order to have enough precision to convert
                # temperature units and avoid setting to 73F will result in 74F
                properties={PROP_MIN_VALUE: hc_min_temp, PROP_MAX_VALUE: hc_max_temp},
            )
        self.char_target_humidity = None
        if CHAR_TARGET_HUMIDITY in self.chars:
            self.char_target_humidity = serv_thermostat.configure_char(
                CHAR_TARGET_HUMIDITY,
                value=50,
                # We do not set a max humidity because
                # homekit currently has a bug that will show the lower bound
                # shifted upwards.  For example if you have a max humidity
                # of 80% homekit will give you the options 20%-100% instead
                # of 0-80%
                properties={PROP_MIN_VALUE: min_humidity},
            )
        self.char_current_humidity = None
        if CHAR_CURRENT_HUMIDITY in self.chars:
            self.char_current_humidity = serv_thermostat.configure_char(
                CHAR_CURRENT_HUMIDITY, value=50
            )

        fan_modes: dict[str, str] = {}
        self.ordered_fan_speeds: list[str] = []

        if features & ClimateEntityFeature.FAN_MODE:
            fan_modes = {
                fan_mode.lower(): fan_mode
                for fan_mode in attributes.get(ATTR_FAN_MODES) or []
            }
            if fan_modes and PRE_DEFINED_FAN_MODES.intersection(fan_modes):
                self.ordered_fan_speeds = [
                    speed for speed in ORDERED_FAN_SPEEDS if speed in fan_modes
                ]
                self.fan_chars.append(CHAR_ROTATION_SPEED)

        if FAN_AUTO in fan_modes and (FAN_ON in fan_modes or self.ordered_fan_speeds):
            self.fan_chars.append(CHAR_TARGET_FAN_STATE)

        self.fan_modes = fan_modes
        if (
            features & ClimateEntityFeature.SWING_MODE
            and (swing_modes := attributes.get(ATTR_SWING_MODES))
            and PRE_DEFINED_SWING_MODES.intersection(swing_modes)
        ):
            self.swing_on_mode = next(
                iter(
                    swing_mode
                    for swing_mode in SWING_MODE_PREFERRED_ORDER
                    if swing_mode in swing_modes
                )
            )
            self.fan_chars.append(CHAR_SWING_MODE)

        if self.fan_chars:
            if attributes.get(ATTR_HVAC_ACTION) is not None:
                self.fan_chars.append(CHAR_CURRENT_FAN_STATE)
            serv_fan = self.add_preload_service(SERV_FANV2, self.fan_chars)
            serv_thermostat.add_linked_service(serv_fan)
            self.char_active = serv_fan.configure_char(
                CHAR_ACTIVE, value=1, setter_callback=self._set_fan_active
            )
            if CHAR_SWING_MODE in self.fan_chars:
                self.char_swing = serv_fan.configure_char(
                    CHAR_SWING_MODE,
                    value=0,
                    setter_callback=self._set_fan_swing_mode,
                )
                self.char_swing.display_name = "Swing Mode"
            if CHAR_ROTATION_SPEED in self.fan_chars:
                self.char_speed = serv_fan.configure_char(
                    CHAR_ROTATION_SPEED,
                    value=100,
                    properties={PROP_MIN_STEP: 100 / len(self.ordered_fan_speeds)},
                    setter_callback=self._set_fan_speed,
                )
                self.char_speed.display_name = "Fan Mode"
            if CHAR_CURRENT_FAN_STATE in self.fan_chars:
                self.char_current_fan_state = serv_fan.configure_char(
                    CHAR_CURRENT_FAN_STATE,
                    value=0,
                )
                self.char_current_fan_state.display_name = "Fan State"
            if CHAR_TARGET_FAN_STATE in self.fan_chars and FAN_AUTO in self.fan_modes:
                self.char_target_fan_state = serv_fan.configure_char(
                    CHAR_TARGET_FAN_STATE,
                    value=0,
                    setter_callback=self._set_fan_auto,
                )
                self.char_target_fan_state.display_name = "Fan Auto"

        self.async_update_state(state)

        serv_thermostat.setter_callback = self._set_chars