async def async_setup_entry(
    hass: HomeAssistant,
    entry: PortainerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Portainer sensors based on a config entry."""
    coordinator = entry.runtime_data

    def _async_add_new_endpoints(endpoints: list[PortainerCoordinatorData]) -> None:
        """Add new endpoint sensor."""
        async_add_entities(
            PortainerEndpointSensor(
                coordinator,
                entity_description,
                endpoint,
            )
            for entity_description in ENDPOINT_SENSORS
            for endpoint in endpoints
            if entity_description.value_fn(endpoint)
        )

    def _async_add_new_containers(
        containers: list[tuple[PortainerCoordinatorData, PortainerContainerData]],
    ) -> None:
        """Add new container sensors."""
        async_add_entities(
            PortainerContainerSensor(
                coordinator,
                entity_description,
                container,
                endpoint,
            )
            for (endpoint, container) in containers
            for entity_description in CONTAINER_SENSORS
        )

    def _async_add_new_stacks(
        stacks: list[tuple[PortainerCoordinatorData, PortainerStackData]],
    ) -> None:
        """Add new stack sensors."""
        async_add_entities(
            PortainerStackSensor(
                coordinator,
                entity_description,
                stack,
                endpoint,
            )
            for (endpoint, stack) in stacks
            for entity_description in STACK_SENSORS
        )

    def _async_add_new_volumes(
        volumes: list[tuple[PortainerCoordinatorData, PortainerVolumeData]],
    ) -> None:
        """Add new volume sensors."""
        async_add_entities(
            PortainerVolumeSensor(
                coordinator,
                entity_description,
                volume.volume,
                endpoint,
            )
            for (endpoint, volume) in volumes
            for entity_description in VOLUME_SENSORS
        )

    coordinator.new_endpoints_callbacks.append(_async_add_new_endpoints)
    coordinator.new_containers_callbacks.append(_async_add_new_containers)
    coordinator.new_stacks_callbacks.append(_async_add_new_stacks)
    coordinator.new_volumes_callbacks.append(_async_add_new_volumes)

    _async_add_new_endpoints(
        [
            endpoint
            for endpoint in coordinator.data.values()
            if endpoint.id in coordinator.known_endpoints
        ]
    )
    _async_add_new_containers(
        [
            (endpoint, container)
            for endpoint in coordinator.data.values()
            for container in endpoint.containers.values()
        ]
    )
    _async_add_new_stacks(
        [
            (endpoint, stack)
            for endpoint in coordinator.data.values()
            for stack in endpoint.stacks.values()
        ]
    )
    _async_add_new_volumes(
        [
            (endpoint, volume)
            for endpoint in coordinator.data.values()
            for volume in endpoint.volumes.values()
        ]
    )