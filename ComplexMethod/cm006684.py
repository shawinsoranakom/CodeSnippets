async def _ensure_port_available(self, port: int, current_project_id: str) -> None:
        """Ensure a port is available, only killing untracked processes.

        Args:
            port: The port number to ensure is available
            current_project_id: The project ID requesting the port

        Raises:
            MCPComposerPortError: If port cannot be made available
            MCPComposerConfigError: If port is invalid
        """
        try:
            is_port_available = self._is_port_available(port)
            await logger.adebug(f"Port {port} availability check: {is_port_available}")
        except (ValueError, OverflowError, TypeError) as e:
            # Port validation failed - invalid port number or type
            # ValueError: from our validation
            # OverflowError: from socket.bind() when port > 65535
            # TypeError: when port is not an integer
            error_msg = f"Invalid port number: {port}. Port must be an integer between 0 and 65535."
            await logger.aerror(f"Invalid port for project {current_project_id}: {e}")
            raise MCPComposerConfigError(error_msg, current_project_id) from e

        if not is_port_available:
            # Check if the port is being used by a tracked project
            is_used_by_other, other_project_id = self._is_port_used_by_another_project(port, current_project_id)

            if is_used_by_other and other_project_id:
                # Port is being used by another tracked project
                # Check if we can take ownership (e.g., the other project is failing)
                other_composer = self.project_composers.get(other_project_id)
                if other_composer and other_composer.get("process"):
                    other_process = other_composer["process"]
                    # If the other process is still running and healthy, don't kill it
                    if other_process.poll() is None:
                        await logger.aerror(
                            f"Port {port} requested by project {current_project_id} is already in use by "
                            f"project {other_project_id}. Will not kill active MCP Composer process."
                        )
                        port_error_msg = (
                            f"Port {port} is already in use by another project. "
                            f"Please choose a different port (e.g., {port + 1}) "
                            f"or disable OAuth on the other project first."
                        )
                        raise MCPComposerPortError(port_error_msg, current_project_id)

                    # Process died but port tracking wasn't cleaned up - allow takeover
                    await logger.adebug(
                        f"Port {port} was tracked to project {other_project_id} but process died. "
                        f"Allowing project {current_project_id} to take ownership."
                    )
                    # Clean up the old tracking
                    await self._do_stop_project_composer(other_project_id)

            # Check if port is used by a process owned by the current project (e.g., stuck in startup loop)
            port_owner_project = self._port_to_project.get(port)
            if port_owner_project == current_project_id:
                # Port is owned by current project - safe to kill
                await logger.adebug(
                    f"Port {port} is in use by current project {current_project_id} (likely stuck in startup). "
                    f"Killing process to retry."
                )
                killed = await self._kill_process_on_port(port)
                if killed:
                    await logger.adebug(
                        f"Successfully killed own process on port {port}. Waiting for port to be released..."
                    )
                    await asyncio.sleep(2)
                    is_port_available = self._is_port_available(port)
                    if not is_port_available:
                        await logger.aerror(f"Port {port} is still in use after killing own process.")
                        port_error_msg = f"Port {port} is still in use after killing process"
                        raise MCPComposerPortError(port_error_msg)
            else:
                # Port is in use by unknown process - don't kill it (security concern)
                await logger.aerror(
                    f"Port {port} is in use by an unknown process (not owned by Langflow). "
                    f"Will not kill external application for security reasons."
                )
                port_error_msg = (
                    f"Port {port} is already in use by another application. "
                    f"Please choose a different port (e.g., {port + 1}) or free up the port manually."
                )
                raise MCPComposerPortError(port_error_msg, current_project_id)

        await logger.adebug(f"Port {port} is available, proceeding with MCP Composer startup")