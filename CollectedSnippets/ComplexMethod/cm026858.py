async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProxmoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ProxmoxVE buttons."""
    coordinator = entry.runtime_data

    def _async_add_new_nodes(nodes: list[ProxmoxNodeData]) -> None:
        """Add new node buttons."""
        async_add_entities(
            ProxmoxNodeButtonEntity(coordinator, entity_description, node)
            for node in nodes
            for entity_description in NODE_BUTTONS
        )

    def _async_add_new_vms(
        vms: list[tuple[ProxmoxNodeData, dict[str, Any]]],
    ) -> None:
        """Add new VM buttons."""
        async_add_entities(
            ProxmoxVMButtonEntity(coordinator, entity_description, vm, node_data)
            for (node_data, vm) in vms
            for entity_description in VM_BUTTONS
        )

    def _async_add_new_containers(
        containers: list[tuple[ProxmoxNodeData, dict[str, Any]]],
    ) -> None:
        """Add new container buttons."""
        async_add_entities(
            ProxmoxContainerButtonEntity(
                coordinator, entity_description, container, node_data
            )
            for (node_data, container) in containers
            for entity_description in CONTAINER_BUTTONS
        )

    coordinator.new_nodes_callbacks.append(_async_add_new_nodes)
    coordinator.new_vms_callbacks.append(_async_add_new_vms)
    coordinator.new_containers_callbacks.append(_async_add_new_containers)

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