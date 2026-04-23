async def _do_start_project_composer(
        self,
        project_id: str,
        streamable_http_url: str,
        auth_config: dict[str, Any] | None,
        max_retries: int = 3,
        max_startup_checks: int = 40,
        startup_delay: float = 2.0,
        *,
        legacy_sse_url: str | None = None,
    ) -> None:
        """Internal method to start an MCP Composer instance.

        Args:
            project_id: The project ID
            streamable_http_url: Streamable HTTP endpoint for the remote Langflow MCP server
            auth_config: Authentication configuration
            max_retries: Maximum number of retry attempts (default: 3)
            max_startup_checks: Number of checks per retry attempt (default: 40)
            startup_delay: Delay between checks in seconds (default: 2.0)
            legacy_sse_url: Optional legacy SSE URL used for backward compatibility

        Raises:
            MCPComposerError: Various specific errors if startup fails
        """
        legacy_sse_url = legacy_sse_url or f"{streamable_http_url.rstrip('/')}/sse"
        if not auth_config:
            no_auth_error_msg = "No auth settings provided"
            raise MCPComposerConfigError(no_auth_error_msg, project_id)

        # Validate OAuth settings early to provide clear error messages
        self._validate_oauth_settings(auth_config)

        project_host = auth_config.get("oauth_host") if auth_config else "unknown"
        project_port = auth_config.get("oauth_port") if auth_config else "unknown"
        await logger.adebug(f"Starting MCP Composer for project {project_id} on {project_host}:{project_port}")

        # Use a per-project lock to prevent race conditions
        if project_id not in self._start_locks:
            self._start_locks[project_id] = asyncio.Lock()

        async with self._start_locks[project_id]:
            # Check if already running (double-check after acquiring lock)
            project_port_str = auth_config.get("oauth_port")
            if not project_port_str:
                no_port_error_msg = "No OAuth port provided"
                raise MCPComposerConfigError(no_port_error_msg, project_id)

            try:
                project_port = int(project_port_str)
            except (ValueError, TypeError) as e:
                port_error_msg = f"Invalid OAuth port: {project_port_str}"
                raise MCPComposerConfigError(port_error_msg, project_id) from e

            project_host = auth_config.get("oauth_host")
            if not project_host:
                no_host_error_msg = "No OAuth host provided"
                raise MCPComposerConfigError(no_host_error_msg, project_id)

            if project_id in self.project_composers:
                composer_info = self.project_composers[project_id]
                process = composer_info.get("process")
                existing_auth = composer_info.get("auth_config", {})
                existing_port = composer_info.get("port")

                # Check if process is still running
                if process and process.poll() is None:
                    # Process is running - only restart if config changed
                    auth_changed = self._has_auth_config_changed(existing_auth, auth_config)

                    if auth_changed:
                        await logger.adebug(f"Config changed for project {project_id}, restarting MCP Composer")
                        await self._do_stop_project_composer(project_id)
                    else:
                        await logger.adebug(
                            f"MCP Composer already running for project {project_id} with current config"
                        )
                        return  # Already running with correct config
                else:
                    # Process died or never started properly, restart it
                    await logger.adebug(f"MCP Composer process died for project {project_id}, restarting")
                    await self._do_stop_project_composer(project_id)
                    # Also kill any process that might be using the old port
                    if existing_port:
                        try:
                            await asyncio.wait_for(self._kill_process_on_port(existing_port), timeout=5.0)
                        except asyncio.TimeoutError:
                            await logger.aerror(f"Timeout while killing process on port {existing_port}")

            # Retry loop: try starting the process multiple times
            last_error = None
            try:
                # Before first attempt, try to kill any zombie MCP Composer processes
                # This is a best-effort operation - don't fail startup if it errors
                try:
                    await logger.adebug(
                        f"Checking for zombie MCP Composer processes on port {project_port} before startup..."
                    )
                    zombies_killed = await self._kill_zombie_mcp_processes(project_port)
                    if zombies_killed:
                        await logger.adebug(f"Killed zombie processes, port {project_port} should now be free")
                except Exception as zombie_error:  # noqa: BLE001
                    # Log but continue - zombie cleanup is optional
                    await logger.awarning(
                        f"Failed to check/kill zombie processes (non-fatal): {zombie_error}. Continuing with startup..."
                    )

                # Ensure port is available (only kill untracked processes)
                try:
                    await self._ensure_port_available(project_port, project_id)
                except (MCPComposerPortError, MCPComposerConfigError) as e:
                    # Port/config error before starting - store and raise immediately (no retries)
                    self._last_errors[project_id] = e.message
                    raise
                for retry_attempt in range(1, max_retries + 1):
                    try:
                        await logger.adebug(
                            f"Starting MCP Composer for project {project_id} (attempt {retry_attempt}/{max_retries})"
                        )

                        # Re-check port availability before each attempt to prevent race conditions
                        if retry_attempt > 1:
                            await logger.adebug(f"Re-checking port {project_port} availability before retry...")
                            await self._ensure_port_available(project_port, project_id)

                        process = await self._start_project_composer_process(
                            project_id,
                            project_host,
                            project_port,
                            streamable_http_url,
                            auth_config,
                            max_startup_checks,
                            startup_delay,
                            legacy_sse_url=legacy_sse_url,
                        )

                    except MCPComposerError as e:
                        last_error = e
                        await logger.aerror(
                            f"MCP Composer startup attempt {retry_attempt}/{max_retries} failed "
                            f"for project {project_id}: {e.message}"
                        )

                        # For config/port errors, don't retry - fail immediately
                        if isinstance(e, (MCPComposerConfigError, MCPComposerPortError)):
                            await logger.aerror(
                                f"Configuration or port error for project {project_id}, not retrying: {e.message}"
                            )
                            raise  # Re-raise to exit retry loop immediately

                        # Clean up any partially started process before retrying
                        if project_id in self.project_composers:
                            await self._do_stop_project_composer(project_id)

                        # If not the last attempt, wait and try to clean up zombie processes
                        if retry_attempt < max_retries:
                            await logger.adebug(f"Waiting 2 seconds before retry attempt {retry_attempt + 1}...")
                            await asyncio.sleep(2)

                            # On Windows, try to kill any zombie MCP Composer processes for this port
                            # This is a best-effort operation - don't fail retry if it errors
                            try:
                                msg = f"Checking for zombie MCP Composer processes on port {project_port}"
                                await logger.adebug(msg)
                                zombies_killed = await self._kill_zombie_mcp_processes(project_port)
                                if zombies_killed:
                                    await logger.adebug(f"Killed zombie processes, port {project_port} should be free")
                            except Exception as retry_zombie_error:  # noqa: BLE001
                                # Log but continue - zombie cleanup is optional
                                msg = f"Failed to check/kill zombie processes during retry: {retry_zombie_error}"
                                await logger.awarning(msg)

                    else:
                        # Success! Store the composer info and register the port and PID
                        self.project_composers[project_id] = {
                            "process": process,
                            "host": project_host,
                            "port": project_port,
                            "streamable_http_url": streamable_http_url,
                            "legacy_sse_url": legacy_sse_url,
                            "sse_url": legacy_sse_url,
                            "auth_config": auth_config,
                        }
                        self._port_to_project[project_port] = project_id
                        self._pid_to_project[process.pid] = project_id
                        # Clear any previous error on success
                        self.clear_last_error(project_id)

                        await logger.adebug(
                            f"MCP Composer started for project {project_id} on port {project_port} "
                            f"(PID: {process.pid}) after {retry_attempt} attempt(s)"
                        )
                        return  # Success!

                # All retries failed, raise the last error
                if last_error:
                    await logger.aerror(
                        f"MCP Composer failed to start for project {project_id} after {max_retries} attempts"
                    )
                    # Store the error message for later retrieval
                    self._last_errors[project_id] = last_error.message
                    raise last_error

            except asyncio.CancelledError:
                # Operation was cancelled, clean up any started process
                await logger.adebug(f"MCP Composer start operation for project {project_id} was cancelled")
                if project_id in self.project_composers:
                    await self._do_stop_project_composer(project_id)
                raise