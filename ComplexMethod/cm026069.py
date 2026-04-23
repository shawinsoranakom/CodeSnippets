def _async_add_remove_endpoints(
        self, mapped_endpoints: dict[int, PortainerCoordinatorData]
    ) -> None:
        """Add new endpoints, remove non-existing endpoints."""
        current_endpoints = {endpoint.id for endpoint in mapped_endpoints.values()}
        self.known_endpoints &= current_endpoints
        new_endpoints = current_endpoints - self.known_endpoints
        if new_endpoints:
            _LOGGER.debug("New endpoints found: %s", new_endpoints)
            self.known_endpoints.update(new_endpoints)
            new_endpoint_data = [
                mapped_endpoints[endpoint_id] for endpoint_id in new_endpoints
            ]
            for endpoint_callback in self.new_endpoints_callbacks:
                endpoint_callback(new_endpoint_data)

        # Surprise, we also handle containers here :)
        current_containers = {
            (endpoint.id, container_name)
            for endpoint in mapped_endpoints.values()
            for container_name in endpoint.containers
        }
        # Prune departed containers so a recreated container is detected as new
        # and its entity is rebuilt with the fresh (ephemeral) Docker container ID.
        self.known_containers &= current_containers
        new_containers = current_containers - self.known_containers
        if new_containers:
            _LOGGER.debug("New containers found: %s", new_containers)
            self.known_containers.update(new_containers)
            new_container_data = [
                (
                    mapped_endpoints[endpoint_id],
                    mapped_endpoints[endpoint_id].containers[name],
                )
                for endpoint_id, name in new_containers
            ]
            for container_callback in self.new_containers_callbacks:
                container_callback(new_container_data)

        # Volume management
        current_volumes = {
            (endpoint.id, volume_name)
            for endpoint in mapped_endpoints.values()
            for volume_name in endpoint.volumes
        }

        self.known_volumes &= current_volumes
        new_volumes = current_volumes - self.known_volumes
        if new_volumes:
            _LOGGER.debug("New volumes found: %s", new_volumes)
            self.known_volumes.update(new_volumes)
            new_volume_data = [
                (
                    mapped_endpoints[endpoint_id],
                    mapped_endpoints[endpoint_id].volumes[name],
                )
                for endpoint_id, name in new_volumes
            ]
            for volume_callback in self.new_volumes_callbacks:
                volume_callback(new_volume_data)

        # Stack management
        current_stacks = {
            (endpoint.id, stack_name)
            for endpoint in mapped_endpoints.values()
            for stack_name in endpoint.stacks
        }

        self.known_stacks &= current_stacks
        new_stacks = current_stacks - self.known_stacks
        if new_stacks:
            _LOGGER.debug("New stacks found: %s", new_stacks)
            self.known_stacks.update(new_stacks)
            new_stack_data = [
                (
                    mapped_endpoints[endpoint_id],
                    mapped_endpoints[endpoint_id].stacks[name],
                )
                for endpoint_id, name in new_stacks
            ]
            for stack_callback in self.new_stacks_callbacks:
                stack_callback(new_stack_data)