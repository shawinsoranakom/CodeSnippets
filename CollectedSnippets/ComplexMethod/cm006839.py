async def run_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Run a tool with the given arguments using context-specific session.

        Args:
            tool_name: Name of the tool to run
            arguments: Dictionary of arguments to pass to the tool

        Returns:
            The result of the tool execution

        Raises:
            ValueError: If session is not initialized or tool execution fails
        """
        if not self._connected or not self._connection_params:
            msg = "Session not initialized or disconnected. Call connect_to_server first."
            raise ValueError(msg)

        # If no session context is set, create a default one
        if not self._session_context:
            # Generate a fallback context based on connection parameters
            import uuid

            param_hash = uuid.uuid4().hex[:8]
            self._session_context = f"default_http_{param_hash}"

        max_retries = 2
        last_error_type = None

        for attempt in range(max_retries):
            try:
                await logger.adebug(f"Attempting to run tool '{tool_name}' (attempt {attempt + 1}/{max_retries})")
                # Get or create persistent session
                session = await self._get_or_create_session()

                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments=arguments),
                    timeout=30.0,  # 30 second timeout
                )
            except Exception as e:
                current_error_type = type(e).__name__
                await logger.awarning(f"Tool '{tool_name}' failed on attempt {attempt + 1}: {current_error_type} - {e}")

                # Import specific MCP error types for detection
                try:
                    from anyio import ClosedResourceError
                    from mcp.shared.exceptions import McpError

                    is_closed_resource_error = isinstance(e, ClosedResourceError)
                    is_mcp_connection_error = isinstance(e, McpError) and "Connection closed" in str(e)
                except ImportError:
                    is_closed_resource_error = "ClosedResourceError" in str(type(e))
                    is_mcp_connection_error = "Connection closed" in str(e)

                # Detect timeout errors
                is_timeout_error = isinstance(e, asyncio.TimeoutError | TimeoutError)

                # If we're getting the same error type repeatedly, don't retry
                if last_error_type == current_error_type and attempt > 0:
                    await logger.aerror(f"Repeated {current_error_type} error for tool '{tool_name}', not retrying")
                    break

                last_error_type = current_error_type

                # If it's a connection error (ClosedResourceError or MCP connection closed) and we have retries left
                if (is_closed_resource_error or is_mcp_connection_error) and attempt < max_retries - 1:
                    await logger.awarning(
                        f"MCP session connection issue for tool '{tool_name}', retrying with fresh session..."
                    )
                    # Clean up the dead session
                    if self._session_context:
                        session_manager = self._get_session_manager()
                        await session_manager._cleanup_session(self._session_context)
                    # Add a small delay before retry
                    await asyncio.sleep(0.5)
                    continue

                # If it's a timeout error and we have retries left, try once more
                if is_timeout_error and attempt < max_retries - 1:
                    await logger.awarning(f"Tool '{tool_name}' timed out, retrying...")
                    # Don't clean up session for timeouts, might just be a slow response
                    await asyncio.sleep(1.0)
                    continue

                # For other errors or no retries left, handle as before
                if (
                    isinstance(e, ConnectionError | TimeoutError | OSError | ValueError)
                    or is_closed_resource_error
                    or is_mcp_connection_error
                    or is_timeout_error
                ):
                    msg = f"Failed to run tool '{tool_name}' after {attempt + 1} attempts: {e}"
                    await logger.aerror(msg)
                    # Clean up failed session from cache
                    if self._session_context and self._component_cache:
                        cache_key = f"mcp_session_http_{self._session_context}"
                        self._component_cache.delete(cache_key)
                    self._connected = False
                    raise ValueError(msg) from e
                # Re-raise unexpected errors
                raise
            else:
                await logger.adebug(f"Tool '{tool_name}' completed successfully")
                return result

        # This should never be reached due to the exception handling above
        msg = f"Failed to run tool '{tool_name}': Maximum retries exceeded with repeated {last_error_type} errors"
        await logger.aerror(msg)
        raise ValueError(msg)