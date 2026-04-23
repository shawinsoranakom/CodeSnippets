async def _do_stop_project_composer(self, project_id: str):
        """Internal method to stop a project composer."""
        if project_id not in self.project_composers:
            return

        composer_info = self.project_composers[project_id]
        process = composer_info.get("process")

        try:
            if process:
                try:
                    # Check if process is still running before trying to terminate
                    if process.poll() is None:
                        await logger.adebug(f"Terminating MCP Composer process {process.pid} for project {project_id}")
                        process.terminate()

                        # Wait longer for graceful shutdown
                        try:
                            await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=2.0)
                            await logger.adebug(f"MCP Composer for project {project_id} terminated gracefully")
                        except asyncio.TimeoutError:
                            await logger.aerror(
                                f"MCP Composer for project {project_id} did not terminate gracefully, force killing"
                            )
                            await asyncio.to_thread(process.kill)
                            await asyncio.to_thread(process.wait)
                    else:
                        await logger.adebug(f"MCP Composer process for project {project_id} was already terminated")

                    await logger.adebug(f"MCP Composer stopped for project {project_id}")

                except ProcessLookupError:
                    # Process already terminated
                    await logger.adebug(f"MCP Composer process for project {project_id} was already terminated")
                except Exception as e:  # noqa: BLE001
                    await logger.aerror(f"Error stopping MCP Composer for project {project_id}: {e}")
        finally:
            # Always clean up tracking, even if stopping failed
            port = composer_info.get("port")
            if port and self._port_to_project.get(port) == project_id:
                self._port_to_project.pop(port, None)
                await logger.adebug(f"Released port {port} from project {project_id}")

            # Clean up PID tracking
            if process and process.pid:
                self._pid_to_project.pop(process.pid, None)
                await logger.adebug(f"Released PID {process.pid} tracking for project {project_id}")

            # Remove from tracking
            self.project_composers.pop(project_id, None)
            await logger.adebug(f"Removed tracking for project {project_id}")