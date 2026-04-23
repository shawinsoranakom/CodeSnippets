async def connect(self) -> None:
        """Start the action_execution_server on the local machine or connect to an existing one."""
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        # Get environment variables for warm server configuration
        desired_num_warm_servers = int(os.getenv('DESIRED_NUM_WARM_SERVERS', '0'))

        # Check if there's already a server running for this session ID
        if self.sid in _RUNNING_SERVERS:
            self.log('info', f'Connecting to existing server for session {self.sid}')
            server_info = _RUNNING_SERVERS[self.sid]
            self.server_process = server_info.process
            self._execution_server_port = server_info.execution_server_port
            self._log_thread = server_info.log_thread
            self._log_thread_exit_event = server_info.log_thread_exit_event
            self._vscode_port = server_info.vscode_port
            self._app_ports = server_info.app_ports
            self._temp_workspace = server_info.temp_workspace
            self.config.workspace_mount_path_in_sandbox = (
                server_info.workspace_mount_path
            )
            self.api_url = (
                f'{self.config.sandbox.local_runtime_url}:{self._execution_server_port}'
            )
        elif self.attach_to_existing:
            # If we're supposed to attach to an existing server but none exists, raise an error
            self.log('error', f'No existing server found for session {self.sid}')
            raise AgentRuntimeDisconnectedError(
                f'No existing server found for session {self.sid}'
            )
        else:
            # Set up workspace directory
            # For local runtime, prefer a stable host path over /workspace defaults.
            if (
                self.config.workspace_base is None
                and self.config.runtime
                and self.config.runtime.lower() == 'local'
            ):
                env_base = os.getenv('LOCAL_WORKSPACE_BASE')
                if env_base:
                    self.config.workspace_base = os.path.abspath(env_base)
                else:
                    self.config.workspace_base = os.path.abspath(
                        os.path.join(os.getcwd(), 'workspace', 'local')
                    )

            if self.config.workspace_base is not None:
                os.makedirs(self.config.workspace_base, exist_ok=True)
                logger.warning(
                    f'Workspace base path is set to {self.config.workspace_base}. '
                    'It will be used as the path for the agent to run in. '
                    'Be careful, the agent can EDIT files in this directory!'
                )
                self.config.workspace_mount_path_in_sandbox = self.config.workspace_base
                self._temp_workspace = None
            else:
                # A temporary directory is created for the agent to run in
                logger.warning(
                    'Workspace base path is NOT set. Agent will run in a temporary directory.'
                )
                self._temp_workspace = tempfile.mkdtemp(
                    prefix=f'openhands_workspace_{self.sid}',
                )
                self.config.workspace_mount_path_in_sandbox = self._temp_workspace

            logger.info(
                f'Using workspace directory: {self.config.workspace_mount_path_in_sandbox}'
            )

            # Check if we have a warm server available
            warm_server_available = False
            if _WARM_SERVERS and not self.attach_to_existing:
                try:
                    # Pop a warm server from the list
                    self.log('info', 'Using a warm server')
                    server_info = _WARM_SERVERS.pop(0)

                    # Use the warm server
                    self.server_process = server_info.process
                    self._execution_server_port = server_info.execution_server_port
                    self._log_thread = server_info.log_thread
                    self._log_thread_exit_event = server_info.log_thread_exit_event
                    self._vscode_port = server_info.vscode_port
                    self._app_ports = server_info.app_ports

                    # We need to clean up the warm server's temp workspace and create a new one
                    if server_info.temp_workspace:
                        shutil.rmtree(server_info.temp_workspace)

                    # Create a new temp workspace for this session
                    if (
                        self._temp_workspace is None
                        and self.config.workspace_base is None
                    ):
                        self._temp_workspace = tempfile.mkdtemp(
                            prefix=f'openhands_workspace_{self.sid}',
                        )
                        self.config.workspace_mount_path_in_sandbox = (
                            self._temp_workspace
                        )

                    self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._execution_server_port}'

                    # Store the server process in the global dictionary with the new workspace
                    _RUNNING_SERVERS[self.sid] = ActionExecutionServerInfo(
                        process=self.server_process,
                        execution_server_port=self._execution_server_port,
                        vscode_port=self._vscode_port,
                        app_ports=self._app_ports,
                        log_thread=self._log_thread,
                        log_thread_exit_event=self._log_thread_exit_event,
                        temp_workspace=self._temp_workspace,
                        workspace_mount_path=self.config.workspace_mount_path_in_sandbox,
                    )

                    warm_server_available = True
                except IndexError:
                    # No warm servers available
                    self.log('info', 'No warm servers available, starting a new server')
                    warm_server_available = False
                except Exception as e:
                    # Error using warm server
                    self.log('error', f'Error using warm server: {e}')
                    warm_server_available = False

            # If no warm server is available, start a new one
            if not warm_server_available:
                # Create a new server
                server_info, api_url = _create_server(
                    config=self.config,
                    plugins=self.plugins,
                    workspace_prefix=self.sid,
                )

                # Set instance variables
                self.server_process = server_info.process
                self._execution_server_port = server_info.execution_server_port
                self._vscode_port = server_info.vscode_port
                self._app_ports = server_info.app_ports
                self._log_thread = server_info.log_thread
                self._log_thread_exit_event = server_info.log_thread_exit_event

                # We need to use the existing temp workspace, not the one created by _create_server
                if (
                    server_info.temp_workspace
                    and server_info.temp_workspace != self._temp_workspace
                ):
                    shutil.rmtree(server_info.temp_workspace)

                self.api_url = api_url

                # Store the server process in the global dictionary with the correct workspace
                _RUNNING_SERVERS[self.sid] = ActionExecutionServerInfo(
                    process=self.server_process,
                    execution_server_port=self._execution_server_port,
                    vscode_port=self._vscode_port,
                    app_ports=self._app_ports,
                    log_thread=self._log_thread,
                    log_thread_exit_event=self._log_thread_exit_event,
                    temp_workspace=self._temp_workspace,
                    workspace_mount_path=self.config.workspace_mount_path_in_sandbox,
                )

        self.log('info', f'Waiting for server to become ready at {self.api_url}...')
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        await call_sync_from_async(self._wait_until_alive)

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'debug',
            f'Server initialized with plugins: {[plugin.name for plugin in self.plugins]}',
        )
        if not self.attach_to_existing:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True

        # Check if we need to create more warm servers after connecting
        if (
            desired_num_warm_servers > 0
            and len(_WARM_SERVERS) < desired_num_warm_servers
        ):
            num_to_create = desired_num_warm_servers - len(_WARM_SERVERS)
            self.log(
                'info',
                f'Creating {num_to_create} additional warm servers to reach desired count',
            )
            for _ in range(num_to_create):
                _create_warm_server_in_background(self.config, self.plugins)