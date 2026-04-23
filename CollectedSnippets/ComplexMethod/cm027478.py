async def async_setup_entry(
    hass: HomeAssistant,
    entry: SystemMonitorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up System Monitor sensors based on a config entry."""
    entities: list[SystemMonitorSensor] = []
    legacy_resources: set[str] = set(entry.options.get("resources", []))
    loaded_resources: set[str] = set()
    coordinator = entry.runtime_data.coordinator
    psutil_wrapper = entry.runtime_data.psutil_wrapper
    sensor_data = coordinator.data

    def get_arguments() -> dict[str, Any]:
        """Return startup information."""
        return {
            "disk_arguments": get_all_disk_mounts(hass, psutil_wrapper),
            "network_arguments": get_all_network_interfaces(hass, psutil_wrapper),
            "fan_speed_arguments": list(sensor_data.fan_speed),
        }

    cpu_temperature: float | None = None
    with contextlib.suppress(AttributeError):
        cpu_temperature = read_cpu_temperature(sensor_data.temperatures)

    startup_arguments = await hass.async_add_executor_job(get_arguments)
    startup_arguments["cpu_temperature"] = cpu_temperature
    startup_arguments["processes"] = entry.options.get(BINARY_SENSOR_DOMAIN, {}).get(
        CONF_PROCESS, []
    )

    _LOGGER.debug("Setup from options %s", entry.options)
    for _type, sensor_description in SENSOR_TYPES.items():
        for sensor_type, sensor_argument in SENSORS_WITH_ARG.items():
            if _type.startswith(sensor_type):
                for argument in startup_arguments[sensor_argument]:
                    is_enabled = check_legacy_resource(
                        f"{_type}_{argument}", legacy_resources
                    )
                    if (_add := slugify(f"{_type}_{argument}")) not in loaded_resources:
                        loaded_resources.add(_add)
                        entities.append(
                            SystemMonitorSensor(
                                coordinator,
                                sensor_description,
                                entry.entry_id,
                                argument,
                                is_enabled,
                            )
                        )
                continue

        if _type.startswith(SENSORS_NO_ARG):
            argument = ""
            is_enabled = check_legacy_resource(f"{_type}_{argument}", legacy_resources)
            loaded_resources.add(slugify(f"{_type}_{argument}"))
            entities.append(
                SystemMonitorSensor(
                    coordinator,
                    sensor_description,
                    entry.entry_id,
                    argument,
                    is_enabled,
                )
            )
            continue

        if _type == "processor_temperature":
            if not startup_arguments["cpu_temperature"]:
                # Don't load processor temperature sensor if we can't read it.
                continue
            argument = ""
            is_enabled = check_legacy_resource(f"{_type}_{argument}", legacy_resources)
            loaded_resources.add(slugify(f"{_type}_{argument}"))
            entities.append(
                SystemMonitorSensor(
                    coordinator,
                    sensor_description,
                    entry.entry_id,
                    argument,
                    is_enabled,
                )
            )
            continue

    # Ensure legacy imported disk_* resources are loaded if they are not part
    # of mount points automatically discovered
    for resource in legacy_resources:
        if resource.startswith("disk_"):
            check_resource = slugify(resource)
            _LOGGER.debug(
                "Check resource %s already loaded in %s",
                check_resource,
                loaded_resources,
            )
            if check_resource not in loaded_resources:
                loaded_resources.add(check_resource)
                split_index = resource.rfind("_")
                _type = resource[:split_index]
                argument = resource[split_index + 1 :]
                _LOGGER.debug("Loading legacy %s with argument %s", _type, argument)
                entities.append(
                    SystemMonitorSensor(
                        coordinator,
                        SENSOR_TYPES[_type],
                        entry.entry_id,
                        argument,
                        True,
                    )
                )

    @callback
    def clean_obsolete_entities() -> None:
        """Remove entities which are disabled and not supported from setup."""
        entity_registry = er.async_get(hass)
        entities = entity_registry.entities.get_entries_for_config_entry_id(
            entry.entry_id
        )
        for entity in entities:
            if (
                entity.unique_id not in loaded_resources
                and entity.disabled is True
                and (
                    entity_id := entity_registry.async_get_entity_id(
                        SENSOR_DOMAIN, DOMAIN, entity.unique_id
                    )
                )
            ):
                entity_registry.async_remove(entity_id)

    clean_obsolete_entities()

    async_add_entities(entities)