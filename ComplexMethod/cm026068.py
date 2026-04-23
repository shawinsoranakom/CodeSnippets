async def _async_update_data(self) -> dict[int, PortainerCoordinatorData]:
        """Fetch data from Portainer API."""
        _LOGGER.debug(
            "Fetching data from Portainer API: %s", self.config_entry.data[CONF_URL]
        )

        try:
            endpoints = await self.portainer.get_endpoints()
        except PortainerAuthenticationError as err:
            _LOGGER.error("Authentication error: %s", repr(err))
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
                translation_placeholders={"error": repr(err)},
            ) from err
        except PortainerConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": repr(err)},
            ) from err

        mapped_endpoints: dict[int, PortainerCoordinatorData] = {}
        for endpoint in endpoints:
            if endpoint.status == EndpointStatus.DOWN:
                _LOGGER.debug(
                    "Skipping offline endpoint: %s (ID: %d)",
                    endpoint.name,
                    endpoint.id,
                )
                continue

            try:
                (
                    containers,
                    docker_version,
                    docker_info,
                    docker_system_df,
                    volumes,
                ) = await asyncio.gather(
                    self.portainer.get_containers(endpoint.id),
                    self.portainer.docker_version(endpoint.id),
                    self.portainer.docker_info(endpoint.id),
                    self.portainer.docker_system_df(endpoint.id, verbose=True),
                    self.portainer.get_volumes(endpoint.id),
                )

                stack_requests = [self.portainer.get_stacks(endpoint_id=endpoint.id)]
                swarm_id = (
                    docker_info.swarm.cluster.get("ID")
                    if docker_info.swarm
                    and docker_info.swarm.control_available
                    and docker_info.swarm.cluster
                    else None
                )
                if swarm_id:
                    stack_requests.append(
                        self.portainer.get_stacks(
                            endpoint_id=endpoint.id, swarm_id=swarm_id
                        )
                    )

                stacks = [
                    stack
                    for result in await asyncio.gather(*stack_requests)
                    for stack in result
                ]

                prev_endpoint = self.data.get(endpoint.id) if self.data else None
                container_map: dict[str, PortainerContainerData] = {}
                stack_map: dict[str, PortainerStackData] = {
                    stack.name: PortainerStackData(stack=stack, container_count=0)
                    for stack in stacks
                }

                volume_usage_map = {
                    item["Name"]: item
                    for item in (docker_system_df.volume_disk_usage.items or [])
                }
                volume_map: dict[str, PortainerVolumeData] = {}
                for volume in volumes:
                    if item := volume_usage_map.get(volume.name):
                        volume.usage_data = DockerVolumeUsageData(
                            size=item["UsageData"]["Size"],
                            ref_count=item["UsageData"]["RefCount"],
                        )
                    volume_map[volume.name] = PortainerVolumeData(volume=volume)

                # Map containers, started and stopped
                for container in containers:
                    container_name = self._get_container_name(container.names[0])
                    prev_container = (
                        prev_endpoint.containers.get(container_name)
                        if prev_endpoint
                        else None
                    )

                    # Check if container belongs to a stack via docker compose label
                    stack_name: str | None = (
                        container.labels.get("com.docker.compose.project")
                        or container.labels.get("com.docker.stack.namespace")
                        if container.labels
                        else None
                    )
                    if stack_name and (stack_data := stack_map.get(stack_name)):
                        stack_data.container_count += 1

                    container_map[container_name] = PortainerContainerData(
                        container=container,
                        stats=None,
                        stats_pre=prev_container.stats if prev_container else None,
                        stack=stack_map[stack_name].stack
                        if stack_name and stack_name in stack_map
                        else None,
                    )

                # Separately fetch stats for active containers
                active_containers = [
                    container
                    for container in containers
                    if container.state
                    in (DockerContainerState.RUNNING, DockerContainerState.PAUSED)
                ]
                if active_containers:
                    container_stats = dict(
                        zip(
                            (
                                self._get_container_name(container.names[0])
                                for container in active_containers
                            ),
                            await asyncio.gather(
                                *(
                                    self.portainer.container_stats(
                                        endpoint_id=endpoint.id,
                                        container_id=container.id,
                                    )
                                    for container in active_containers
                                )
                            ),
                            strict=False,
                        )
                    )

                    # Now assign stats to the containers
                    for container_name, stats in container_stats.items():
                        container_map[container_name].stats = stats
            except PortainerConnectionError as err:
                _LOGGER.exception("Connection error")
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="cannot_connect",
                    translation_placeholders={"error": repr(err)},
                ) from err
            except PortainerAuthenticationError as err:
                _LOGGER.exception("Authentication error")
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="invalid_auth",
                    translation_placeholders={"error": repr(err)},
                ) from err

            mapped_endpoints[endpoint.id] = PortainerCoordinatorData(
                id=endpoint.id,
                name=endpoint.name,
                endpoint=endpoint,
                containers=container_map,
                docker_version=docker_version,
                docker_info=docker_info,
                docker_system_df=docker_system_df,
                volumes=volume_map,
                stacks=stack_map,
            )

        self._async_add_remove_endpoints(mapped_endpoints)

        return mapped_endpoints