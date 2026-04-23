def init_container(self) -> None:
        self.log('debug', 'Preparing to start container...')
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        # Allocate host port with locking to prevent race conditions
        self._host_port, self._host_port_lock = self._find_available_port_with_lock(
            EXECUTION_SERVER_PORT_RANGE
        )
        self._container_port = self._host_port

        # Use the configured vscode_port if provided, otherwise find an available port
        if self.config.sandbox.vscode_port:
            self._vscode_port = self.config.sandbox.vscode_port
            self._vscode_port_lock = None  # No lock needed for configured port
        else:
            self._vscode_port, self._vscode_port_lock = (
                self._find_available_port_with_lock(VSCODE_PORT_RANGE)
            )

        # Allocate app ports with locking
        app_port_1, app_lock_1 = self._find_available_port_with_lock(APP_PORT_RANGE_1)
        app_port_2, app_lock_2 = self._find_available_port_with_lock(APP_PORT_RANGE_2)

        self._app_ports = [app_port_1, app_port_2]
        self._app_port_locks = [
            lock for lock in [app_lock_1, app_lock_2] if lock is not None
        ]

        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'

        use_host_network = self.config.sandbox.use_host_network
        network_mode: typing.Literal['host'] | None = (
            'host' if use_host_network else None
        )

        # Initialize port mappings
        port_mapping: dict[str, list[dict[str, str]]] | None = None
        if not use_host_network:
            port_mapping = {
                f'{self._container_port}/tcp': [
                    {
                        'HostPort': str(self._host_port),
                        'HostIp': self.config.sandbox.runtime_binding_address,
                    }
                ],
            }

            if self.vscode_enabled:
                port_mapping[f'{self._vscode_port}/tcp'] = [
                    {
                        'HostPort': str(self._vscode_port),
                        'HostIp': self.config.sandbox.runtime_binding_address,
                    }
                ]

            for port in self._app_ports:
                port_mapping[f'{port}/tcp'] = [
                    {
                        'HostPort': str(port),
                        'HostIp': self.config.sandbox.runtime_binding_address,
                    }
                ]
        else:
            self.log(
                'warn',
                'Using host network mode. If you are using MacOS, please make sure you have the latest version of Docker Desktop and enabled host network feature: https://docs.docker.com/network/drivers/host/#docker-desktop',
            )

        # Combine environment variables
        environment = dict(**self.initial_env_vars)
        environment.update(
            {
                'port': str(self._container_port),
                'PYTHONUNBUFFERED': '1',
                # Passing in the ports means nested runtimes do not come up with their own ports!
                'VSCODE_PORT': str(self._vscode_port),
                'APP_PORT_1': str(self._app_ports[0]),
                'APP_PORT_2': str(self._app_ports[1]),
                'OPENHANDS_SESSION_ID': str(self.sid),
                'PIP_BREAK_SYSTEM_PACKAGES': '1',
            }
        )
        if self.config.debug or DEBUG:
            environment['DEBUG'] = 'true'
        # Pass DOCKER_HOST_ADDR to spawned containers if it exists
        if os.environ.get('DOCKER_HOST_ADDR'):
            environment['DOCKER_HOST_ADDR'] = os.environ['DOCKER_HOST_ADDR']
        # also update with runtime_startup_env_vars
        environment.update(self.config.sandbox.runtime_startup_env_vars)

        self.log('debug', f'Workspace Base: {self.config.workspace_base}')

        # Process volumes for mounting
        volumes = self._process_volumes()

        # If no volumes were configured, set to None
        if not volumes:
            logger.debug(
                'Mount dir is not set, will not mount the workspace directory to the container'
            )
            volumes = {}  # Empty dict instead of None to satisfy mypy
        self.log(
            'debug',
            f'Sandbox workspace: {self.config.workspace_mount_path_in_sandbox}',
        )

        command = self.get_action_execution_server_startup_command()
        self.log('info', f'Starting server with command: {command}')

        if self.config.sandbox.enable_gpu:
            gpu_ids = self.config.sandbox.cuda_visible_devices
            if gpu_ids is None:
                device_requests = [
                    docker.types.DeviceRequest(capabilities=[['gpu']], count=-1)
                ]
            else:
                device_requests = [
                    docker.types.DeviceRequest(
                        capabilities=[['gpu']],
                        device_ids=[str(i) for i in gpu_ids.split(',')],
                    )
                ]
        else:
            device_requests = None
        try:
            if self.runtime_container_image is None:
                raise ValueError('Runtime container image is not set')
            # Process overlay mounts (read-only lower with per-container COW)
            overlay_mounts = self._process_overlay_mounts()

            self.container = self.docker_client.containers.run(
                self.runtime_container_image,
                # Use Docker's tini init process to ensure proper signal handling and reaping of
                # zombie child processes.
                init=True,
                command=command,
                # Override the default 'bash' entrypoint because the command is a binary.
                entrypoint=[],
                network_mode=network_mode,
                ports=port_mapping,
                working_dir='/openhands/code/',  # do not change this!
                name=self.container_name,
                detach=True,
                environment=environment,
                volumes=volumes,  # type: ignore
                mounts=overlay_mounts,  # type: ignore
                device_requests=device_requests,
                **(self.config.sandbox.docker_runtime_kwargs or {}),
            )
            self.log('debug', f'Container started. Server url: {self.api_url}')
            self.set_runtime_status(RuntimeStatus.RUNTIME_STARTED)
        except Exception as e:
            self.log(
                'error',
                f'Error: Instance {self.container_name} FAILED to start container!\n',
            )
            self.close()
            raise e