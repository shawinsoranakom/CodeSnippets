async def _wait_for_sandbox_start(
        self, task: AppConversationStartTask
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        """Wait for sandbox to start and return info."""
        # Get or create the sandbox
        if not task.request.sandbox_id:
            # First try to find a running sandbox for the current user
            sandbox = await self._find_running_sandbox_for_user()
            if sandbox is None:
                # No running sandbox found, start a new one

                # Convert conversation_id to hex string if present
                sandbox_id_str = (
                    task.request.conversation_id.hex
                    if task.request.conversation_id is not None
                    else None
                )

                sandbox = await self.sandbox_service.start_sandbox(
                    sandbox_id=sandbox_id_str
                )
            task.sandbox_id = sandbox.id
        else:
            sandbox_info = await self.sandbox_service.get_sandbox(
                task.request.sandbox_id
            )
            if sandbox_info is None:
                raise SandboxError(f'Sandbox not found: {task.request.sandbox_id}')
            sandbox = sandbox_info

        # Update the listener with sandbox info
        task.status = AppConversationStartTaskStatus.WAITING_FOR_SANDBOX
        task.sandbox_id = sandbox.id

        # Log sandbox assignment for observability
        conversation_id_str = (
            str(task.request.conversation_id)
            if task.request.conversation_id is not None
            else 'unknown'
        )
        _logger.info(
            f'Assigned sandbox {sandbox.id} to conversation {conversation_id_str}'
        )

        yield task

        # Resume if paused
        if sandbox.status == SandboxStatus.PAUSED:
            await self.sandbox_service.resume_sandbox(sandbox.id)

        # Check for immediate error states
        if sandbox.status in (None, SandboxStatus.ERROR):
            raise SandboxError(f'Sandbox status: {sandbox.status}')

        # For non-STARTING/RUNNING states (except PAUSED which we just resumed), fail fast
        if sandbox.status not in (
            SandboxStatus.STARTING,
            SandboxStatus.RUNNING,
            SandboxStatus.PAUSED,
        ):
            raise SandboxError(f'Sandbox not startable: {sandbox.id}')

        # Use shared wait_for_sandbox_running utility to poll for ready state
        await self.sandbox_service.wait_for_sandbox_running(
            sandbox.id,
            timeout=self.sandbox_startup_timeout,
            poll_interval=self.sandbox_startup_poll_frequency,
            httpx_client=self.httpx_client,
        )