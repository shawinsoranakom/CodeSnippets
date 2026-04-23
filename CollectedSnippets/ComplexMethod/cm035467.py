def _start_or_attach_to_runtime(self) -> None:
        self.log('info', 'Starting or attaching to runtime')
        existing_runtime = self._check_existing_runtime()
        if existing_runtime:
            self.log('info', f'Using existing runtime with ID: {self.runtime_id}')
        elif self.attach_to_existing:
            self.log('info', f'Failed to find existing runtime for SID: {self.sid}')
            raise AgentRuntimeNotFoundError(
                f'Could not find existing runtime for SID: {self.sid}'
            )
        else:
            self.log('info', 'No existing runtime found, starting a new one')
            if self.config.sandbox.runtime_container_image is None:
                self.log(
                    'info',
                    f'Building remote runtime with base image: {self.config.sandbox.base_container_image}',
                )
                self._build_runtime()
            else:
                self.log(
                    'info',
                    f'Starting remote runtime with image: {self.config.sandbox.runtime_container_image}',
                )
                self.container_image = self.config.sandbox.runtime_container_image
            self._start_runtime()
        assert self.runtime_id is not None, (
            'Runtime ID is not set. This should never happen.'
        )
        assert self.runtime_url is not None, (
            'Runtime URL is not set. This should never happen.'
        )
        if not self.attach_to_existing:
            self.log('info', 'Waiting for runtime to be alive...')
        self._wait_until_alive()
        if not self.attach_to_existing:
            self.log('info', 'Runtime is ready.')
        self.set_runtime_status(RuntimeStatus.READY)