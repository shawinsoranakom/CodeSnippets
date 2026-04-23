async def async_save_data(self):
        """Save the device configuration to `hass.data`."""
        binary_sensors = {}
        for entity in self.options.get(CONF_BINARY_SENSORS) or []:
            zone = entity[CONF_ZONE]

            binary_sensors[zone] = {
                CONF_TYPE: entity[CONF_TYPE],
                CONF_NAME: entity.get(
                    CONF_NAME, f"Konnected {self.device_id[6:]} Zone {zone}"
                ),
                CONF_INVERSE: entity.get(CONF_INVERSE),
                ATTR_STATE: None,
            }
            _LOGGER.debug(
                "Set up binary_sensor %s (initial state: %s)",
                binary_sensors[zone].get("name"),
                binary_sensors[zone].get(ATTR_STATE),
            )

        actuators = []
        for entity in self.options.get(CONF_SWITCHES) or []:
            zone = entity[CONF_ZONE]

            act = {
                CONF_ZONE: zone,
                CONF_NAME: entity.get(
                    CONF_NAME,
                    f"Konnected {self.device_id[6:]} Actuator {zone}",
                ),
                ATTR_STATE: None,
                CONF_ACTIVATION: entity[CONF_ACTIVATION],
                CONF_MOMENTARY: entity.get(CONF_MOMENTARY),
                CONF_PAUSE: entity.get(CONF_PAUSE),
                CONF_REPEAT: entity.get(CONF_REPEAT),
            }
            actuators.append(act)
            _LOGGER.debug("Set up switch %s", act)

        sensors = []
        for entity in self.options.get(CONF_SENSORS) or []:
            zone = entity[CONF_ZONE]

            sensor = {
                CONF_ZONE: zone,
                CONF_NAME: entity.get(
                    CONF_NAME, f"Konnected {self.device_id[6:]} Sensor {zone}"
                ),
                CONF_TYPE: entity[CONF_TYPE],
                CONF_POLL_INTERVAL: entity.get(CONF_POLL_INTERVAL),
            }
            sensors.append(sensor)
            _LOGGER.debug(
                "Set up %s sensor %s (initial state: %s)",
                sensor.get(CONF_TYPE),
                sensor.get(CONF_NAME),
                sensor.get(ATTR_STATE),
            )

        device_data = {
            CONF_BINARY_SENSORS: binary_sensors,
            CONF_SENSORS: sensors,
            CONF_SWITCHES: actuators,
            CONF_BLINK: self.options.get(CONF_BLINK),
            CONF_DISCOVERY: self.options.get(CONF_DISCOVERY),
            CONF_HOST: self.host,
            CONF_PORT: self.port,
            "panel": self,
        }

        if CONF_DEVICES not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][CONF_DEVICES] = {}

        _LOGGER.debug(
            "Storing data in hass.data[%s][%s][%s]: %s",
            DOMAIN,
            CONF_DEVICES,
            self.device_id,
            device_data,
        )
        self.hass.data[DOMAIN][CONF_DEVICES][self.device_id] = device_data