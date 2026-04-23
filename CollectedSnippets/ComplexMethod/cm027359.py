def add_to_platform_start(
        self,
        hass: HomeAssistant,
        platform: EntityPlatform,
        parallel_updates: asyncio.Semaphore | None,
    ) -> None:
        """Start adding an entity to a platform.

        Allows integrations to remove legacy custom unit conversion which is no longer
        needed without breaking existing sensors. Only works for sensors which are in
        the entity registry.

        This can be removed once core integrations have dropped unneeded custom unit
        conversion.
        """
        super().add_to_platform_start(hass, platform, parallel_updates)

        # Bail out if the sensor doesn't have a unique_id or a device class
        if self.unique_id is None or self.device_class is None:
            return
        registry = er.async_get(self.hass)

        # Bail out if the entity is not yet registered
        if not (
            entity_id := registry.async_get_entity_id(
                platform.domain, platform.platform_name, self.unique_id
            )
        ):
            # Prime _sensor_option_unit_of_measurement to ensure the correct unit
            # is stored in the entity registry.
            self._sensor_option_unit_of_measurement = self._get_initial_suggested_unit()
            return

        registry_entry = registry.async_get(entity_id)
        assert registry_entry

        # Prime _sensor_option_unit_of_measurement to ensure the correct unit
        # is stored in the entity registry.
        self.registry_entry = registry_entry
        self._async_read_entity_options()

        # If the sensor has 'unit_of_measurement' in its sensor options, the user has
        # overridden the unit.
        # If the sensor has 'sensor.private' in its entity options, it already has a
        # suggested_unit.
        registry_unit = registry_entry.unit_of_measurement
        if (
            (
                (sensor_options := registry_entry.options.get(DOMAIN))
                and CONF_UNIT_OF_MEASUREMENT in sensor_options
            )
            or f"{DOMAIN}.private" in registry_entry.options
            or self.unit_of_measurement == registry_unit
        ):
            return

        # Make sure we can convert the units
        if (
            (unit_converter := UNIT_CONVERTERS.get(self.device_class)) is None
            or registry_unit not in unit_converter.VALID_UNITS
            or self.unit_of_measurement not in unit_converter.VALID_UNITS
        ):
            return

        # Set suggested_unit_of_measurement to the old unit to enable automatic
        # conversion
        self.registry_entry = registry.async_update_entity_options(
            entity_id,
            f"{DOMAIN}.private",
            {"suggested_unit_of_measurement": registry_unit},
        )
        # Update _sensor_option_unit_of_measurement to ensure the correct unit
        # is stored in the entity registry.
        self._async_read_entity_options()