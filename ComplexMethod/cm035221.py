async def _container_to_sandbox_info(self, container) -> SandboxInfo | None:
        """Convert Docker container to SandboxInfo."""
        # Convert Docker status to runtime status
        status = self._docker_status_to_sandbox_status(container.status)

        # Parse creation time
        created_str = container.attrs.get('Created', '')
        try:
            created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            created_at = utc_now()

        # Get URL and session key for running containers
        exposed_urls = None
        session_api_key = None

        if status == SandboxStatus.RUNNING:
            # Get session API key first
            env = self._get_container_env_vars(container)
            session_api_key = env.get(SESSION_API_KEY_VARIABLE)

            # Get the exposed port mappings
            exposed_urls = []

            # Check if container is using host network mode
            network_mode = container.attrs.get('HostConfig', {}).get('NetworkMode', '')
            is_host_network = network_mode == 'host'

            if is_host_network:
                # Host network mode: container ports are directly accessible on host
                for exposed_port in self.exposed_ports:
                    host_port = exposed_port.container_port
                    url = self.container_url_pattern.format(port=host_port)

                    # VSCode URLs require the api_key and working dir
                    if exposed_port.name == VSCODE:
                        url += f'/?tkn={session_api_key}&folder={container.attrs["Config"]["WorkingDir"]}'

                    exposed_urls.append(
                        ExposedUrl(
                            name=exposed_port.name,
                            url=url,
                            port=exposed_port.container_port,
                        )
                    )
            else:
                # Bridge network mode: use port bindings
                port_bindings = container.attrs.get('NetworkSettings', {}).get(
                    'Ports', {}
                )
                if port_bindings:
                    for container_port, host_bindings in port_bindings.items():
                        if host_bindings:
                            host_port = int(host_bindings[0]['HostPort'])
                            matching_port = next(
                                (
                                    ep
                                    for ep in self.exposed_ports
                                    if container_port == f'{ep.container_port}/tcp'
                                ),
                                None,
                            )
                            if matching_port:
                                url = self.container_url_pattern.format(port=host_port)

                                # VSCode URLs require the api_key and working dir
                                if matching_port.name == VSCODE:
                                    url += f'/?tkn={session_api_key}&folder={container.attrs["Config"]["WorkingDir"]}'

                                exposed_urls.append(
                                    ExposedUrl(
                                        name=matching_port.name,
                                        url=url,
                                        port=matching_port.container_port,
                                    )
                                )

        if not container.image.tags:
            _logger.debug(
                f'Skipping container {container.name!r}: image has no tags (image id: {container.image.id})'
            )
            return None

        return SandboxInfo(
            id=container.name,
            created_by_user_id=None,
            sandbox_spec_id=container.image.tags[0],
            status=status,
            session_api_key=session_api_key,
            exposed_urls=exposed_urls,
            created_at=created_at,
        )