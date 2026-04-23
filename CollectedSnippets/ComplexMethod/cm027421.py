def set_sensors_used_in_climate(
        self, device_ids: list[str], preset_mode: str | None = None
    ) -> None:
        """Set the sensors used on a climate for a thermostat."""
        if preset_mode is None:
            preset_mode = self.preset_mode

        # Check if climate is an available preset option.
        elif preset_mode not in self._preset_modes.values():
            if self.preset_modes:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_preset",
                    translation_placeholders={
                        "options": ", ".join(self._preset_modes.values())
                    },
                )

        # Get device name from device id.
        device_registry = dr.async_get(self.hass)
        sensor_names: list[str] = []
        sensor_ids: list[str] = []
        for device_id in device_ids:
            device = device_registry.async_get(device_id)
            if device and device.name:
                r_sensors = self.thermostat.get("remoteSensors", [])
                ecobee_identifier = next(
                    (
                        identifier
                        for identifier in device.identifiers
                        if identifier[0] == "ecobee"
                    ),
                    None,
                )
                if ecobee_identifier:
                    code = ecobee_identifier[1]
                    for r_sensor in r_sensors:
                        if (  # occurs if remote sensor
                            len(code) == 4 and r_sensor.get("code") == code
                        ) or (  # occurs if thermostat
                            len(code) != 4 and r_sensor.get("type") == "thermostat"
                        ):
                            sensor_ids.append(r_sensor.get("id"))  # noqa: PERF401
                    sensor_names.append(device.name)

        # Ensure sensors provided are available for thermostat or not empty.
        if not set(sensor_names).issubset(set(self._sensors)) or not sensor_names:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_sensor",
                translation_placeholders={
                    "options": ", ".join(
                        [
                            f"{item['name_by_user']} ({item['id']})"
                            for item in self.remote_sensor_ids_names
                        ]
                    )
                },
            )

        # Check that an id was found for each sensor
        if len(device_ids) != len(sensor_ids):
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="sensor_lookup_failed"
            )

        # Check if sensors are currently used on the climate for the thermostat.
        current_sensors_in_climate = self._sensors_in_preset_mode(preset_mode)
        if set(sensor_names) == set(current_sensors_in_climate):
            _LOGGER.debug(
                "This action would not be an update, current sensors on climate (%s) are: %s",
                preset_mode,
                ", ".join(current_sensors_in_climate),
            )
            return

        _LOGGER.debug(
            "Setting sensors %s to be used on thermostat %s for program %s",
            sensor_names,
            self.device_info.get("name"),
            preset_mode,
        )
        self.data.ecobee.update_climate_sensors(
            self.thermostat_index, preset_mode, sensor_ids=sensor_ids
        )
        self.update_without_throttle = True