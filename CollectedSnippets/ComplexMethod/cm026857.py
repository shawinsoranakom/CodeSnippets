async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProxmoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Proxmox VE sensors."""
    coordinator = entry.runtime_data

    def _async_add_new_nodes(nodes: list[ProxmoxNodeData]) -> None:
        """Add new node sensors."""
        async_add_entities(
            ProxmoxNodeSensor(coordinator, entity_description, node)
            for node in nodes
            for entity_description in NODE_SENSORS
        )

    def _async_add_new_vms(
        vms: list[tuple[ProxmoxNodeData, dict[str, Any]]],
    ) -> None:
        """Add new VM sensors."""
        async_add_entities(
            ProxmoxVMSensor(coordinator, entity_description, vm, node_data)
            for (node_data, vm) in vms
            for entity_description in VM_SENSORS
        )

    def _async_add_new_containers(
        containers: list[tuple[ProxmoxNodeData, dict[str, Any]]],
    ) -> None:
        """Add new container sensors."""
        async_add_entities(
            ProxmoxContainerSensor(
                coordinator, entity_description, container, node_data
            )
            for (node_data, container) in containers
            for entity_description in CONTAINER_SENSORS
        )

    def _async_add_new_storages(
        storages: list[tuple[ProxmoxNodeData, dict[str, Any]]],
    ) -> None:
        """Add new storage sensors."""
        async_add_entities(
            ProxmoxStorageSensor(coordinator, entity_description, storage, node_data)
            for (node_data, storage) in storages
            for entity_description in STORAGE_SENSORS
        )

    coordinator.new_nodes_callbacks.append(_async_add_new_nodes)
    coordinator.new_vms_callbacks.append(_async_add_new_vms)
    coordinator.new_containers_callbacks.append(_async_add_new_containers)
    coordinator.new_storages_callbacks.append(_async_add_new_storages)

    _async_add_new_nodes(
        [
            node_data
            for node_data in coordinator.data.values()
            if node_data.node["node"] in coordinator.known_nodes
        ]
    )
    _async_add_new_vms(
        [
            (node_data, vm_data)
            for node_data in coordinator.data.values()
            for vmid, vm_data in node_data.vms.items()
            if (node_data.node["node"], vmid) in coordinator.known_vms
        ]
    )
    _async_add_new_containers(
        [
            (node_data, container_data)
            for node_data in coordinator.data.values()
            for vmid, container_data in node_data.containers.items()
            if (node_data.node["node"], vmid) in coordinator.known_containers
        ]
    )
    _async_add_new_storages(
        [
            (node_data, storage_data)
            for node_data in coordinator.data.values()
            for storage_name, storage_data in node_data.storages.items()
            if (node_data.node["node"], storage_name) in coordinator.known_storages
        ]
    )