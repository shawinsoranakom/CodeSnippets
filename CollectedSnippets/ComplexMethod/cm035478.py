async def execute_action(self, action: Action) -> Observation:
        """Execute an action by sending it to the server."""
        if not self.runtime_initialized:
            raise AgentRuntimeDisconnectedError('Runtime not initialized')

        # Check if our server process is still valid
        if self.server_process is None:
            # Check if there's a server in the global dictionary
            if self.sid in _RUNNING_SERVERS:
                self.server_process = _RUNNING_SERVERS[self.sid].process
            else:
                raise AgentRuntimeDisconnectedError('Server process not found')

        # Check if the server process is still running
        if self.server_process.poll() is not None:
            # If the process died, remove it from the global dictionary
            if self.sid in _RUNNING_SERVERS:
                del _RUNNING_SERVERS[self.sid]
            raise AgentRuntimeDisconnectedError('Server process died')

        with self.action_semaphore:
            try:
                response = await call_sync_from_async(
                    lambda: self.session.post(
                        f'{self.api_url}/execute_action',
                        json={'action': event_to_dict(action)},
                    )
                )

                # After executing the action, check if we need to create more warm servers
                desired_num_warm_servers = int(
                    os.getenv('DESIRED_NUM_WARM_SERVERS', '0')
                )
                if (
                    desired_num_warm_servers > 0
                    and len(_WARM_SERVERS) < desired_num_warm_servers
                ):
                    self.log(
                        'info',
                        f'Creating a new warm server to maintain desired count of {desired_num_warm_servers}',
                    )
                    _create_warm_server_in_background(self.config, self.plugins)

                return observation_from_dict(response.json())
            except httpx.NetworkError:
                raise AgentRuntimeDisconnectedError('Server connection lost')