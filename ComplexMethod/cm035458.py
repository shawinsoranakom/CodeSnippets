async def connect(self):
        """Connect to the runtime by creating or attaching to a pod."""
        self.log('info', f'Connecting to runtime with conversation ID: {self.sid}')
        self.log('info', f'self._attach_to_existing: {self.attach_to_existing}')
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
        self.log('info', f'Using API URL {self.api_url}')

        try:
            await call_sync_from_async(self._attach_to_pod)
        except client.rest.ApiException as e:
            # we are not set to attach to existing, ignore error and init k8s resources.
            if self.attach_to_existing:
                self.log(
                    'error',
                    f'Pod {self.pod_name} not found or cannot connect to it.',
                )
                raise AgentRuntimeDisconnectedError from e

            self.log('info', f'Starting runtime with image: {self.pod_image}')
            try:
                await call_sync_from_async(self._init_k8s_resources)
                self.log(
                    'info',
                    f'Pod started: {self.pod_name}. VSCode URL: {self.vscode_url}',
                )
            except Exception as init_error:
                self.log('error', f'Failed to initialize k8s resources: {init_error}')
                raise AgentRuntimeNotFoundError(
                    f'Failed to initialize kubernetes resources: {init_error}'
                ) from init_error

        if not self.attach_to_existing:
            self.log('info', 'Waiting for pod to become ready ...')
            self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
        try:
            await call_sync_from_async(self._wait_until_ready)
        except Exception as alive_error:
            self.log('error', f'Failed to connect to runtime: {alive_error}')
            self.set_runtime_status(
                RuntimeStatus.ERROR_RUNTIME_DISCONNECTED,
                f'Failed to connect to runtime: {alive_error}',
            )
            raise AgentRuntimeDisconnectedError(
                f'Failed to connect to runtime: {alive_error}'
            ) from alive_error

        if not self.attach_to_existing:
            self.log('info', 'Runtime is ready.')

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'info',
            f'Pod initialized with plugins: {[plugin.name for plugin in self.plugins]}. VSCode URL: {self.vscode_url}',
        )
        if not self.attach_to_existing:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True