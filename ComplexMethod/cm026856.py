def _async_add_remove_nodes(self, data: dict[str, ProxmoxNodeData]) -> None:
        """Add new nodes/VMs/containers, track removals."""
        current_nodes = set(data.keys())
        self.known_nodes &= current_nodes
        new_nodes = current_nodes - self.known_nodes
        if new_nodes:
            _LOGGER.debug("New nodes found: %s", new_nodes)
            self.known_nodes.update(new_nodes)
            new_node_data = [data[node_name] for node_name in new_nodes]
            for nodes_callback in self.new_nodes_callbacks:
                nodes_callback(new_node_data)

        # And yes, track new VM's and containers as well
        current_vms = {
            (node_name, vmid)
            for node_name, node_data in data.items()
            for vmid in node_data.vms
        }
        self.known_vms &= current_vms
        new_vms = current_vms - self.known_vms
        if new_vms:
            _LOGGER.debug("New VMs found: %s", new_vms)
            self.known_vms.update(new_vms)
            new_vm_data = [
                (data[node_name], data[node_name].vms[vmid])
                for node_name, vmid in new_vms
            ]
            for vms_callback in self.new_vms_callbacks:
                vms_callback(new_vm_data)

        current_containers = {
            (node_name, vmid)
            for node_name, node_data in data.items()
            for vmid in node_data.containers
        }
        self.known_containers &= current_containers
        new_containers = current_containers - self.known_containers
        if new_containers:
            _LOGGER.debug("New containers found: %s", new_containers)
            self.known_containers.update(new_containers)
            new_container_data = [
                (data[node_name], data[node_name].containers[vmid])
                for node_name, vmid in new_containers
            ]
            for containers_callback in self.new_containers_callbacks:
                containers_callback(new_container_data)

        current_storages = {
            (node_name, storage_name)
            for node_name, node_data in data.items()
            for storage_name in node_data.storages
        }
        self.known_storages &= current_storages
        new_storages = current_storages - self.known_storages
        if new_storages:
            _LOGGER.debug("New storages found: %s", new_storages)
            self.known_storages.update(new_storages)
            new_storage_data = [
                (data[node_name], data[node_name].storages[storage_name])
                for node_name, storage_name in new_storages
            ]
            for storages_callback in self.new_storages_callbacks:
                storages_callback(new_storage_data)