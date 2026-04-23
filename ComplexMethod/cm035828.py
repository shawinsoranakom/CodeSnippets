async def connect(self):
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
        should_start_action_execution_server = False

        if self.attach_to_existing:
            self.sandbox = await call_sync_from_async(self._get_sandbox)
        else:
            should_start_action_execution_server = True

        if self.sandbox is None:
            self.set_runtime_status(RuntimeStatus.BUILDING_RUNTIME)
            self.sandbox = await call_sync_from_async(self._create_sandbox)
            self.log("info", f"Created a new sandbox with id: {self.sid}")

        self.api_url = self._construct_api_url(self._sandbox_port)

        state = self.sandbox.state

        if state == "stopping":
            self.log("info", "Waiting for the Daytona sandbox to stop...")
            await call_sync_from_async(self.sandbox.wait_for_sandbox_stop)
            state = "stopped"

        if state == "stopped":
            self.log("info", "Starting the Daytona sandbox...")
            await call_sync_from_async(self.sandbox.start)
            should_start_action_execution_server = True

        if should_start_action_execution_server:
            await call_sync_from_async(self._start_action_execution_server)
            self.log(
                "info",
                f"Container started. Action execution server url: {self.api_url}",
            )

        self.log("info", "Waiting for client to become ready...")
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
        await call_sync_from_async(self._wait_until_alive)

        if should_start_action_execution_server:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            "info",
            f"Container initialized with plugins: {[plugin.name for plugin in self.plugins]}",
        )

        if should_start_action_execution_server:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True