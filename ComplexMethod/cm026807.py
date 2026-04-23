def create_services(self) -> Service:
        """Create and configure the primary service for this accessory."""
        self.chars.append(CHAR_ACTIVE)
        self.chars.append(CHAR_CURRENT_AIR_PURIFIER_STATE)
        self.chars.append(CHAR_TARGET_AIR_PURIFIER_STATE)
        serv_air_purifier = self.add_preload_service(SERV_AIR_PURIFIER, self.chars)
        self.set_primary_service(serv_air_purifier)

        self.char_active: Characteristic = serv_air_purifier.configure_char(
            CHAR_ACTIVE, value=0
        )

        self.preset_mode_chars: dict[str, Characteristic]
        self.char_current_humidity: Characteristic | None = None
        self.char_pm25_density: Characteristic | None = None
        self.char_current_temperature: Characteristic | None = None
        self.char_filter_change_indication: Characteristic | None = None
        self.char_filter_life_level: Characteristic | None = None

        self.char_target_air_purifier_state: Characteristic = (
            serv_air_purifier.configure_char(
                CHAR_TARGET_AIR_PURIFIER_STATE,
                value=0,
            )
        )

        self.char_current_air_purifier_state: Characteristic = (
            serv_air_purifier.configure_char(
                CHAR_CURRENT_AIR_PURIFIER_STATE,
                value=0,
            )
        )

        self.linked_humidity_sensor = self.config.get(CONF_LINKED_HUMIDITY_SENSOR)
        if self.linked_humidity_sensor:
            humidity_serv = self.add_preload_service(SERV_HUMIDITY_SENSOR, CHAR_NAME)
            serv_air_purifier.add_linked_service(humidity_serv)
            self.char_current_humidity = humidity_serv.configure_char(
                CHAR_CURRENT_HUMIDITY, value=0
            )

            humidity_state = self.hass.states.get(self.linked_humidity_sensor)
            if humidity_state:
                self._async_update_current_humidity(humidity_state)

        self.linked_pm25_sensor = self.config.get(CONF_LINKED_PM25_SENSOR)
        if self.linked_pm25_sensor:
            pm25_serv = self.add_preload_service(
                SERV_AIR_QUALITY_SENSOR,
                [CHAR_AIR_QUALITY, CHAR_NAME, CHAR_PM25_DENSITY],
            )
            serv_air_purifier.add_linked_service(pm25_serv)
            self.char_pm25_density = pm25_serv.configure_char(
                CHAR_PM25_DENSITY, value=0
            )

            self.char_air_quality = pm25_serv.configure_char(CHAR_AIR_QUALITY)

            pm25_state = self.hass.states.get(self.linked_pm25_sensor)
            if pm25_state:
                self._async_update_current_pm25(pm25_state)

        self.linked_temperature_sensor = self.config.get(CONF_LINKED_TEMPERATURE_SENSOR)
        if self.linked_temperature_sensor:
            temperature_serv = self.add_preload_service(
                SERV_TEMPERATURE_SENSOR, [CHAR_NAME, CHAR_CURRENT_TEMPERATURE]
            )
            serv_air_purifier.add_linked_service(temperature_serv)
            self.char_current_temperature = temperature_serv.configure_char(
                CHAR_CURRENT_TEMPERATURE, value=0
            )

            temperature_state = self.hass.states.get(self.linked_temperature_sensor)
            if temperature_state:
                self._async_update_current_temperature(temperature_state)

        self.linked_filter_change_indicator_binary_sensor = self.config.get(
            CONF_LINKED_FILTER_CHANGE_INDICATION
        )
        self.linked_filter_life_level_sensor = self.config.get(
            CONF_LINKED_FILTER_LIFE_LEVEL
        )
        if (
            self.linked_filter_change_indicator_binary_sensor
            or self.linked_filter_life_level_sensor
        ):
            chars = [CHAR_NAME, CHAR_FILTER_CHANGE_INDICATION]
            if self.linked_filter_life_level_sensor:
                chars.append(CHAR_FILTER_LIFE_LEVEL)
            serv_filter_maintenance = self.add_preload_service(
                SERV_FILTER_MAINTENANCE, chars
            )
            serv_air_purifier.add_linked_service(serv_filter_maintenance)
            serv_filter_maintenance.configure_char(
                CHAR_NAME,
                value=cleanup_name_for_homekit(f"{self.display_name} Filter"),
            )

            self.char_filter_change_indication = serv_filter_maintenance.configure_char(
                CHAR_FILTER_CHANGE_INDICATION,
                value=0,
            )

            if self.linked_filter_change_indicator_binary_sensor:
                filter_change_indicator_state = self.hass.states.get(
                    self.linked_filter_change_indicator_binary_sensor
                )
                if filter_change_indicator_state:
                    self._async_update_filter_change_indicator(
                        filter_change_indicator_state
                    )

            if self.linked_filter_life_level_sensor:
                self.char_filter_life_level = serv_filter_maintenance.configure_char(
                    CHAR_FILTER_LIFE_LEVEL,
                    value=0,
                )

                filter_life_level_state = self.hass.states.get(
                    self.linked_filter_life_level_sensor
                )
                if filter_life_level_state:
                    self._async_update_filter_life_level(filter_life_level_state)

        return serv_air_purifier