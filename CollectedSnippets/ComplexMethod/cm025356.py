def async_setup_rpc_attribute_entities(
    hass: HomeAssistant,
    config_entry: ShellyConfigEntry,
    async_add_entities: AddEntitiesCallback,
    sensors: Mapping[str, RpcEntityDescription],
    sensor_class: Callable,
) -> None:
    """Set up entities for RPC attributes."""
    coordinator = config_entry.runtime_data.rpc
    assert coordinator

    polling_coordinator = None
    if not (sleep_period := config_entry.data[CONF_SLEEP_PERIOD]):
        polling_coordinator = config_entry.runtime_data.rpc_poll
        assert polling_coordinator

    entities = []
    for sensor_id in sensors:
        description = sensors[sensor_id]
        key_instances = get_rpc_key_instances(
            coordinator.device.status, description.key
        )

        for key in key_instances:
            # Filter non-existing sensors
            if description.models and coordinator.model not in description.models:
                continue

            if description.role and description.role != get_rpc_role_by_key(
                coordinator.device.config, key
            ):
                continue

            if (
                description.sub_key
                and description.sub_key not in coordinator.device.status[key]
                and not description.supported(coordinator.device.status[key])
            ):
                continue

            # Filter and remove entities that according to settings/status
            # should not create an entity
            if description.removal_condition and description.removal_condition(
                coordinator.device.config, coordinator.device.status, key
            ):
                entity_class = get_entity_class(sensor_class, description)
                domain = entity_class.__module__.split(".")[-1]
                unique_id = entity_class(
                    coordinator, key, sensor_id, description
                ).unique_id
                LOGGER.debug("Removing Shelly entity with unique_id: %s", unique_id)
                async_remove_shelly_entity(hass, domain, unique_id)
            elif description.use_polling_coordinator:
                if not sleep_period:
                    entities.append(
                        get_entity_class(sensor_class, description)(
                            polling_coordinator, key, sensor_id, description
                        )
                    )
            else:
                entities.append(
                    get_entity_class(sensor_class, description)(
                        coordinator, key, sensor_id, description
                    )
                )
    if not entities:
        return

    async_add_entities(entities)