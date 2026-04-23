def _async_configure_linked_sensors(
        self,
        ent_reg_ent: er.RegistryEntry,
        lookup: dict[tuple[str, str | None], str],
        state: State,
    ) -> None:
        if (ent_reg_ent.device_class or ent_reg_ent.original_device_class) in (
            BinarySensorDeviceClass.BATTERY_CHARGING,
            SensorDeviceClass.BATTERY,
        ):
            return

        domain = state.domain
        attributes = state.attributes
        config = self._config
        entity_id = state.entity_id

        if ATTR_BATTERY_CHARGING not in attributes and (
            battery_charging_binary_sensor_entity_id := lookup.get(
                BATTERY_CHARGING_SENSOR
            )
        ):
            config[entity_id].setdefault(
                CONF_LINKED_BATTERY_CHARGING_SENSOR,
                battery_charging_binary_sensor_entity_id,
            )

        if ATTR_BATTERY_LEVEL not in attributes and (
            battery_sensor_entity_id := lookup.get(BATTERY_SENSOR)
        ):
            config[entity_id].setdefault(
                CONF_LINKED_BATTERY_SENSOR, battery_sensor_entity_id
            )

        if domain == CAMERA_DOMAIN:
            if motion_event_entity_id := lookup.get(MOTION_EVENT_SENSOR):
                config[entity_id].setdefault(
                    CONF_LINKED_MOTION_SENSOR, motion_event_entity_id
                )
            elif motion_binary_sensor_entity_id := lookup.get(MOTION_SENSOR):
                config[entity_id].setdefault(
                    CONF_LINKED_MOTION_SENSOR, motion_binary_sensor_entity_id
                )

        if domain in (CAMERA_DOMAIN, LOCK_DOMAIN):
            if doorbell_event_entity_id := lookup.get(DOORBELL_EVENT_SENSOR):
                config[entity_id].setdefault(
                    CONF_LINKED_DOORBELL_SENSOR, doorbell_event_entity_id
                )

        if domain == FAN_DOMAIN:
            if current_humidity_sensor_entity_id := lookup.get(HUMIDITY_SENSOR):
                config[entity_id].setdefault(
                    CONF_LINKED_HUMIDITY_SENSOR, current_humidity_sensor_entity_id
                )
            if current_pm25_sensor_entity_id := lookup.get(PM25_SENSOR):
                config[entity_id].setdefault(CONF_TYPE, TYPE_AIR_PURIFIER)
                config[entity_id].setdefault(
                    CONF_LINKED_PM25_SENSOR, current_pm25_sensor_entity_id
                )
            if current_temperature_sensor_entity_id := lookup.get(TEMPERATURE_SENSOR):
                config[entity_id].setdefault(
                    CONF_LINKED_TEMPERATURE_SENSOR, current_temperature_sensor_entity_id
                )

        if domain == HUMIDIFIER_DOMAIN and (
            current_humidity_sensor_entity_id := lookup.get(HUMIDITY_SENSOR)
        ):
            config[entity_id].setdefault(
                CONF_LINKED_HUMIDITY_SENSOR, current_humidity_sensor_entity_id
            )