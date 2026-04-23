def async_update_items(self):
        """Update sensors from the bridge."""
        api = self.bridge.api.sensors

        if len(self._component_add_entities) < len(self._enabled_platforms):
            return

        to_add = {}
        primary_sensor_devices = {}
        current = self.current

        # Physical Hue motion sensors present as three sensors in the API: a
        # presence sensor, a temperature sensor, and a light level sensor. Of
        # these, only the presence sensor is assigned the user-friendly name
        # that the user has given to the device. Each of these sensors is
        # linked by a common device_id, which is the first twenty-three
        # characters of the unique id (then followed by a hyphen and an ID
        # specific to the individual sensor).
        #
        # To set up neat values, and assign the sensor entities to the same
        # device, we first, iterate over all the sensors and find the Hue
        # presence sensors, then iterate over all the remaining sensors -
        # finding the remaining ones that may or may not be related to the
        # presence sensors.
        for item_id in api:
            if api[item_id].type != TYPE_ZLL_PRESENCE:
                continue

            primary_sensor_devices[_device_id(api[item_id])] = api[item_id]

        # Iterate again now we have all the presence sensors, and add the
        # related sensors with nice names where appropriate.
        for item_id in api:
            uniqueid = api[item_id].uniqueid
            if current.get(uniqueid, self.current_events.get(uniqueid)) is not None:
                continue

            sensor_type = api[item_id].type

            # Check for event generator devices
            event_config = EVENT_CONFIG_MAP.get(sensor_type)
            if event_config is not None:
                base_name = api[item_id].name
                name = event_config["name_format"].format(base_name)
                new_event = event_config["class"](api[item_id], name, self.bridge)
                self.bridge.hass.async_create_task(
                    new_event.async_update_device_registry()
                )
                self.current_events[uniqueid] = new_event

            sensor_config = SENSOR_CONFIG_MAP.get(sensor_type)
            if sensor_config is None:
                continue

            base_name = api[item_id].name
            primary_sensor = primary_sensor_devices.get(_device_id(api[item_id]))
            if primary_sensor is not None:
                base_name = primary_sensor.name
            name = sensor_config["name_format"].format(base_name)

            current[uniqueid] = sensor_config["class"](
                api[item_id], name, self.bridge, primary_sensor=primary_sensor
            )

            to_add.setdefault(sensor_config["platform"], []).append(current[uniqueid])

        self.bridge.hass.async_create_task(
            remove_devices(
                self.bridge,
                [value.uniqueid for value in api.values()],
                current,
            )
        )

        for platform, value in to_add.items():
            self._component_add_entities[platform](value)