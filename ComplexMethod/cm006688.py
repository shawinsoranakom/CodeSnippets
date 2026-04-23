async def _start_project_composer_process(
        self,
        project_id: str,
        host: str,
        port: int,
        streamable_http_url: str,
        auth_config: dict[str, Any] | None = None,
        max_startup_checks: int = 40,
        startup_delay: float = 2.0,
        *,
        legacy_sse_url: str | None = None,
    ) -> subprocess.Popen:
        """Start the MCP Composer subprocess for a specific project.

        Args:
            project_id: The project ID
            host: Host to bind to
            port: Port to bind to
            streamable_http_url: Streamable HTTP endpoint to connect to
            auth_config: Authentication configuration
            max_startup_checks: Number of port binding checks (default: 40)
            startup_delay: Delay between checks in seconds (default: 2.0)
            legacy_sse_url: Optional legacy SSE URL used for backward compatibility when required by tooling

        Returns:
            The started subprocess

        Raises:
            MCPComposerStartupError: If startup fails
        """
        settings = get_settings_service().settings
        # Some composer tooling still uses the --sse-url flag for backwards compatibility even in HTTP mode.
        effective_legacy_sse_url = legacy_sse_url or f"{streamable_http_url.rstrip('/')}/sse"

        cmd = [
            "uvx",
            f"mcp-composer{settings.mcp_composer_version}",
            "--port",
            str(port),
            "--host",
            host,
            "--mode",
            "http",
            "--endpoint",
            streamable_http_url,
            "--sse-url",
            effective_legacy_sse_url,
            "--disable-composer-tools",
        ]

        # Set environment variables
        env = os.environ.copy()

        oauth_server_url = auth_config.get("oauth_server_url") if auth_config else None
        if auth_config:
            auth_type = auth_config.get("auth_type")

            if auth_type == "oauth":
                cmd.extend(["--auth_type", "oauth"])

                # Add OAuth environment variables as command line arguments
                cmd.extend(["--env", "ENABLE_OAUTH", "True"])

                # Map auth config to environment variables for OAuth
                # Note: oauth_host and oauth_port are passed both via --host/--port CLI args
                # (for server binding) and as environment variables (for OAuth flow)
                # Note: mcp-composer expects the env var name OAUTH_CALLBACK_PATH, but the value
                # is still the full callback URL used as the OAuth redirect_uri. Support legacy
                # oauth_callback_path input for backwards compatibility.
                oauth_env_mapping = {
                    "oauth_host": "OAUTH_HOST",
                    "oauth_port": "OAUTH_PORT",
                    "oauth_server_url": "OAUTH_SERVER_URL",
                    "oauth_callback_path": "OAUTH_CALLBACK_PATH",
                    "oauth_client_id": "OAUTH_CLIENT_ID",
                    "oauth_client_secret": "OAUTH_CLIENT_SECRET",  # pragma: allowlist secret
                    "oauth_auth_url": "OAUTH_AUTH_URL",
                    "oauth_token_url": "OAUTH_TOKEN_URL",
                    "oauth_mcp_scope": "OAUTH_MCP_SCOPE",
                    "oauth_provider_scope": "OAUTH_PROVIDER_SCOPE",
                }

                normalized_auth_config = self._normalize_oauth_callback_aliases(auth_config)

                # Add environment variables as command line arguments
                # Only set non-empty values to avoid Pydantic validation errors
                for config_key, env_key in oauth_env_mapping.items():
                    value = normalized_auth_config.get(config_key)
                    if value is not None and str(value).strip():
                        cmd.extend(["--env", env_key, str(value)])

        # Log the command being executed (with secrets obfuscated)
        safe_cmd = self._obfuscate_command_secrets(cmd)
        await logger.adebug(f"Starting MCP Composer with command: {' '.join(safe_cmd)}")

        # Start the subprocess with both stdout and stderr captured
        # On Windows, use temp files to avoid pipe buffering issues that can cause process to hang
        stdout_handle: int | typing.IO[bytes] = subprocess.PIPE
        stderr_handle: int | typing.IO[bytes] = subprocess.PIPE
        stdout_file = None
        stderr_file = None

        if platform.system() == "Windows":
            # Create temp files for stdout/stderr on Windows to avoid pipe deadlocks
            # Note: We intentionally don't use context manager as we need files to persist
            # for the subprocess and be cleaned up manually later
            stdout_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                mode="w+b", delete=False, prefix=f"mcp_composer_{project_id}_stdout_", suffix=".log"
            )
            stderr_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                mode="w+b", delete=False, prefix=f"mcp_composer_{project_id}_stderr_", suffix=".log"
            )
            stdout_handle = stdout_file
            stderr_handle = stderr_file
            stdout_name = stdout_file.name
            stderr_name = stderr_file.name
            await logger.adebug(f"Using temp files for MCP Composer logs: stdout={stdout_name}, stderr={stderr_name}")

        process = subprocess.Popen(cmd, env=env, stdout=stdout_handle, stderr=stderr_handle)  # noqa: ASYNC220, S603

        # Monitor the process startup with multiple checks
        process_running = False
        port_bound = False

        await logger.adebug(
            f"MCP Composer process started with PID {process.pid}, monitoring startup for project {project_id}..."
        )

        try:
            for check in range(max_startup_checks):
                await asyncio.sleep(startup_delay)

                # Check if process is still running
                poll_result = process.poll()

                startup_error_msg = None
                if poll_result is not None:
                    # Process terminated, get the error output
                    (
                        stdout_content,
                        stderr_content,
                        startup_error_msg,
                    ) = await self._read_process_output_and_extract_error(
                        process, oauth_server_url, stdout_file=stdout_file, stderr_file=stderr_file
                    )
                    await self._log_startup_error_details(
                        project_id, cmd, host, port, stdout_content, stderr_content, startup_error_msg, poll_result
                    )
                    raise MCPComposerStartupError(startup_error_msg, project_id)

                # Process is still running, check if port is bound
                port_bound = not self._is_port_available(port)

                if port_bound:
                    await logger.adebug(
                        f"MCP Composer for project {project_id} bound to port {port} "
                        f"(check {check + 1}/{max_startup_checks})"
                    )
                    process_running = True
                    break
                await logger.adebug(
                    f"MCP Composer for project {project_id} not yet bound to port {port} "
                    f"(check {check + 1}/{max_startup_checks})"
                )

                # Try to read any available stderr/stdout without blocking to see what's happening
                await self._read_stream_non_blocking(process.stderr, "stderr")
                await self._read_stream_non_blocking(process.stdout, "stdout")

        except asyncio.CancelledError:
            # Operation was cancelled, kill the process and cleanup
            await logger.adebug(
                f"MCP Composer process startup cancelled for project {project_id}, terminating process {process.pid}"
            )
            try:
                process.terminate()
                # Wait for graceful termination with timeout
                try:
                    await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=2.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination times out
                    await logger.adebug(f"Process {process.pid} did not terminate gracefully, force killing")
                    await asyncio.to_thread(process.kill)
                    await asyncio.to_thread(process.wait)
            except Exception as e:  # noqa: BLE001
                await logger.adebug(f"Error terminating process during cancellation: {e}")
            raise  # Re-raise to propagate cancellation

        # After all checks
        if not process_running or not port_bound:
            # Get comprehensive error information
            poll_result = process.poll()

            if poll_result is not None:
                # Process died
                stdout_content, stderr_content, startup_error_msg = await self._read_process_output_and_extract_error(
                    process, oauth_server_url, stdout_file=stdout_file, stderr_file=stderr_file
                )
                await self._log_startup_error_details(
                    project_id, cmd, host, port, stdout_content, stderr_content, startup_error_msg, poll_result
                )
                raise MCPComposerStartupError(startup_error_msg, project_id)
            # Process running but port not bound
            await logger.aerror(
                f"  - Checked {max_startup_checks} times over {max_startup_checks * startup_delay} seconds"
            )

            # Get any available output before terminating
            process.terminate()
            stdout_content, stderr_content, startup_error_msg = await self._read_process_output_and_extract_error(
                process, oauth_server_url, stdout_file=stdout_file, stderr_file=stderr_file
            )
            await self._log_startup_error_details(
                project_id, cmd, host, port, stdout_content, stderr_content, startup_error_msg, pid=process.pid
            )
            raise MCPComposerStartupError(startup_error_msg, project_id)

        # Close the pipes/files if everything is successful
        if stdout_file and stderr_file:
            # Clean up temp files on success
            try:
                stdout_file.close()
                stderr_file.close()
                Path(stdout_file.name).unlink()
                Path(stderr_file.name).unlink()
            except Exception as e:  # noqa: BLE001
                await logger.adebug(f"Error cleaning up temp files on success: {e}")
        else:
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()

        return process