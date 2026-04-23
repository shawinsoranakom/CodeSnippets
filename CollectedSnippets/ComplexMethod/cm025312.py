async def async_setup_entry(
    hass: HomeAssistant,
    entry: WithingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor config entry."""
    ent_reg = er.async_get(hass)

    withings_data = entry.runtime_data

    measurement_coordinator = withings_data.measurement_coordinator

    entities: list[SensorEntity] = []
    entities.extend(
        WithingsMeasurementSensor(measurement_coordinator, description)
        for measurement_type in measurement_coordinator.data
        if (description := get_measurement_description(measurement_type)) is not None
    )

    current_measurement_types = set(measurement_coordinator.data)

    def _async_measurement_listener() -> None:
        """Listen for new measurements and add sensors if they did not exist."""
        received_measurement_types = set(measurement_coordinator.data)
        new_measurement_types = received_measurement_types - current_measurement_types
        if new_measurement_types:
            current_measurement_types.update(new_measurement_types)
            async_add_entities(
                WithingsMeasurementSensor(measurement_coordinator, description)
                for measurement_type in new_measurement_types
                if (description := get_measurement_description(measurement_type))
                is not None
            )

    measurement_coordinator.async_add_listener(_async_measurement_listener)

    goals_coordinator = withings_data.goals_coordinator

    current_goals = get_current_goals(goals_coordinator.data)

    entities.extend(
        WithingsGoalsSensor(goals_coordinator, GOALS_SENSORS[goal])
        for goal in current_goals
    )

    def _async_goals_listener() -> None:
        """Listen for new goals and add sensors if they did not exist."""
        received_goals = get_current_goals(goals_coordinator.data)
        new_goals = received_goals - current_goals
        if new_goals:
            current_goals.update(new_goals)
            async_add_entities(
                WithingsGoalsSensor(goals_coordinator, GOALS_SENSORS[goal])
                for goal in new_goals
            )

    goals_coordinator.async_add_listener(_async_goals_listener)

    activity_coordinator = withings_data.activity_coordinator

    activity_entities_setup_before = ent_reg.async_get_entity_id(
        Platform.SENSOR, DOMAIN, f"withings_{entry.unique_id}_activity_steps_today"
    )

    if activity_coordinator.data is not None or activity_entities_setup_before:
        entities.extend(
            WithingsActivitySensor(activity_coordinator, attribute)
            for attribute in ACTIVITY_SENSORS
        )
    else:
        remove_activity_listener: Callable[[], None]

        def _async_add_activity_entities() -> None:
            """Add activity entities."""
            if activity_coordinator.data is not None:
                async_add_entities(
                    WithingsActivitySensor(activity_coordinator, attribute)
                    for attribute in ACTIVITY_SENSORS
                )
                remove_activity_listener()

        remove_activity_listener = activity_coordinator.async_add_listener(
            _async_add_activity_entities
        )

    sleep_coordinator = withings_data.sleep_coordinator

    sleep_entities_setup_before = ent_reg.async_get_entity_id(
        Platform.SENSOR,
        DOMAIN,
        f"withings_{entry.unique_id}_sleep_deep_duration_seconds",
    )

    if sleep_coordinator.data is not None or sleep_entities_setup_before:
        entities.extend(
            WithingsSleepSensor(sleep_coordinator, attribute)
            for attribute in SLEEP_SENSORS
        )
    else:
        remove_sleep_listener: Callable[[], None]

        def _async_add_sleep_entities() -> None:
            """Add sleep entities."""
            if sleep_coordinator.data is not None:
                async_add_entities(
                    WithingsSleepSensor(sleep_coordinator, attribute)
                    for attribute in SLEEP_SENSORS
                )
                remove_sleep_listener()

        remove_sleep_listener = sleep_coordinator.async_add_listener(
            _async_add_sleep_entities
        )

    workout_coordinator = withings_data.workout_coordinator

    workout_entities_setup_before = ent_reg.async_get_entity_id(
        Platform.SENSOR, DOMAIN, f"withings_{entry.unique_id}_workout_type"
    )

    if workout_coordinator.data is not None or workout_entities_setup_before:
        entities.extend(
            WithingsWorkoutSensor(workout_coordinator, attribute)
            for attribute in WORKOUT_SENSORS
        )
    else:
        remove_workout_listener: Callable[[], None]

        def _async_add_workout_entities() -> None:
            """Add workout entities."""
            if workout_coordinator.data is not None:
                async_add_entities(
                    WithingsWorkoutSensor(workout_coordinator, attribute)
                    for attribute in WORKOUT_SENSORS
                )
                remove_workout_listener()

        remove_workout_listener = workout_coordinator.async_add_listener(
            _async_add_workout_entities
        )

    device_coordinator = withings_data.device_coordinator

    current_devices: set[str] = set()

    def _async_device_listener() -> None:
        """Add device entities."""
        received_devices = set(device_coordinator.data)
        new_devices = received_devices - current_devices
        old_devices = current_devices - received_devices
        if new_devices:
            device_registry = dr.async_get(hass)
            for device_id in new_devices:
                if device := device_registry.async_get_device({(DOMAIN, device_id)}):
                    if any(
                        (
                            config_entry := hass.config_entries.async_get_entry(
                                config_entry_id
                            )
                        )
                        and config_entry.state == ConfigEntryState.LOADED
                        for config_entry_id in device.config_entries
                    ):
                        continue
                async_add_entities(
                    WithingsDeviceSensor(device_coordinator, description, device_id)
                    for description in DEVICE_SENSORS
                )
                current_devices.add(device_id)

        if old_devices:
            device_registry = dr.async_get(hass)
            for device_id in old_devices:
                if device := device_registry.async_get_device({(DOMAIN, device_id)}):
                    device_registry.async_update_device(
                        device.id, remove_config_entry_id=entry.entry_id
                    )
                    current_devices.remove(device_id)

    device_coordinator.async_add_listener(_async_device_listener)

    _async_device_listener()

    if not entities:
        LOGGER.warning(
            "No data found for Withings entry %s, sensors will be added when new data is available",
            entry.title,
        )

    async_add_entities(entities)