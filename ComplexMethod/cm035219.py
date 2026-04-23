async def wait_for_sandbox_running(
        self,
        sandbox_id: str,
        timeout: int = 120,
        poll_interval: int = 2,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> SandboxInfo:
        """Wait for a sandbox to reach RUNNING status with an alive agent server.

        This method polls the sandbox status until it reaches RUNNING state and
        optionally verifies the agent server is responding to health checks.

        Args:
            sandbox_id: The sandbox ID to wait for
            timeout: Maximum time to wait in seconds (default: 120)
            poll_interval: Time between status checks in seconds (default: 2)
            httpx_client: Optional httpx client for agent server health checks.
                If provided, will verify the agent server /alive endpoint responds
                before returning.

        Returns:
            SandboxInfo with RUNNING status and verified agent server

        Raises:
            SandboxError: If sandbox not found, enters ERROR state, or times out
        """
        start = time.time()
        while time.time() - start <= timeout:
            sandbox = await self.get_sandbox(sandbox_id)
            if sandbox is None:
                raise SandboxError(f'Sandbox not found: {sandbox_id}')

            if sandbox.status == SandboxStatus.ERROR:
                raise SandboxError(f'Sandbox entered error state: {sandbox_id}')

            if sandbox.status == SandboxStatus.RUNNING:
                # Optionally verify agent server is alive to avoid race conditions
                # where sandbox reports RUNNING but agent server isn't ready yet
                if httpx_client and sandbox.exposed_urls:
                    if await self._check_agent_server_alive(sandbox, httpx_client):
                        return sandbox
                    # Agent server not ready yet, continue polling
                else:
                    return sandbox

            await asyncio.sleep(poll_interval)

        raise SandboxError(f'Sandbox failed to start within {timeout}s: {sandbox_id}')