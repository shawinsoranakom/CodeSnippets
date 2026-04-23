async def start_sandbox(
        self, sandbox_spec_id: str | None = None, sandbox_id: str | None = None
    ) -> SandboxInfo:
        """Start a new sandbox."""
        # Warn about port collision risk when using host network mode with multiple sandboxes
        if self.use_host_network and self.max_num_sandboxes > 1:
            _logger.warning(
                'Host network mode is enabled with max_num_sandboxes > 1. '
                'Multiple sandboxes will attempt to bind to the same ports, '
                'which may cause port collision errors. Consider setting '
                'max_num_sandboxes=1 when using host network mode.'
            )

        # Enforce sandbox limits by cleaning up old sandboxes
        await self.pause_old_sandboxes(self.max_num_sandboxes - 1)

        if sandbox_spec_id is None:
            sandbox_spec = await self.sandbox_spec_service.get_default_sandbox_spec()
        else:
            sandbox_spec_maybe = await self.sandbox_spec_service.get_sandbox_spec(
                sandbox_spec_id
            )
            if sandbox_spec_maybe is None:
                raise ValueError('Sandbox Spec not found')
            sandbox_spec = sandbox_spec_maybe

        # Generate a sandbox id if none was provided
        if sandbox_id is None:
            sandbox_id = base62.encodebytes(os.urandom(16))

        # Generate container name and session api key
        container_name = f'{self.container_name_prefix}{sandbox_id}'
        session_api_key = base62.encodebytes(os.urandom(32))

        # Prepare environment variables
        env_vars = sandbox_spec.initial_env.copy()
        env_vars[SESSION_API_KEY_VARIABLE] = session_api_key
        env_vars[WEBHOOK_CALLBACK_VARIABLE] = (
            f'http://host.docker.internal:{self.host_port}/api/v1/webhooks'
        )

        # Set CORS origins for remote browser access when web_url is configured.
        # This allows the agent-server container to accept requests from the
        # frontend when running OpenHands on a remote machine.
        # Each origin gets its own indexed env var (OH_ALLOW_CORS_ORIGINS_0, _1, etc.)
        cors_origins: list[str] = []
        if self.web_url:
            cors_origins.append(self.web_url)
        cors_origins.extend(self.permitted_cors_origins)
        # Deduplicate while preserving order
        seen: set[str] = set()
        for origin in cors_origins:
            if origin not in seen:
                seen.add(origin)
                idx = len(seen) - 1
                env_vars[f'OH_ALLOW_CORS_ORIGINS_{idx}'] = origin

        # Prepare port mappings and add port environment variables
        # When using host network, container ports are directly accessible on the host
        # so we use the container ports directly instead of mapping to random host ports
        port_mappings: dict[int, int] | None = None
        if self.use_host_network:
            # Host network mode: container ports are directly accessible
            for exposed_port in self.exposed_ports:
                env_vars[exposed_port.name] = str(exposed_port.container_port)
        else:
            # Bridge network mode: map container ports to random host ports
            port_mappings = {}
            for exposed_port in self.exposed_ports:
                host_port = self._find_unused_port()
                port_mappings[exposed_port.container_port] = host_port
                env_vars[exposed_port.name] = str(exposed_port.container_port)

        # Prepare labels
        labels = {
            'sandbox_spec_id': sandbox_spec.id,
        }

        # Prepare volumes
        volumes = {
            mount.host_path: {
                'bind': mount.container_path,
                'mode': mount.mode,
            }
            for mount in self.mounts
        }

        # Determine network mode
        network_mode = 'host' if self.use_host_network else None

        if self.use_host_network:
            _logger.info(f'Starting sandbox {container_name} with host network mode')

        # Determine devices to pass through (e.g., /dev/kvm for hardware virtualization)
        devices = ['/dev/kvm:/dev/kvm:rwm'] if self.kvm_enabled else None

        if self.kvm_enabled:
            _logger.info(
                f'Starting sandbox {container_name} with KVM device passthrough'
            )

        try:
            # Create and start the container
            container = self.docker_client.containers.run(  # type: ignore[call-overload,misc]
                image=sandbox_spec.id,
                command=sandbox_spec.command,  # Use default command from image
                remove=False,
                name=container_name,
                environment=env_vars,
                ports=port_mappings,
                volumes=volumes,
                working_dir=sandbox_spec.working_dir,
                labels=labels,
                detach=True,
                # Use Docker's tini init process to ensure proper signal handling and reaping of
                # zombie child processes.
                init=True,
                # Allow agent-server containers to resolve host.docker.internal
                # and other custom hostnames for LAN deployments
                # Note: extra_hosts is not needed with host network mode
                extra_hosts=self.extra_hosts
                if self.extra_hosts and not self.use_host_network
                else None,
                # Network mode: 'host' for host networking, None for default bridge
                network_mode=network_mode,
                # Device passthrough for KVM hardware virtualization
                devices=devices,
            )

            sandbox_info = await self._container_to_sandbox_info(container)
            assert sandbox_info is not None
            return sandbox_info

        except APIError as e:
            raise SandboxError(f'Failed to start container: {e}')