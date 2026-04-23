async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        """Intercept and control async tool execution with retry logic.

        Args:
            request: Tool call request with call `dict`, `BaseTool`, state, and runtime.
            handler: Async callable to execute the tool and returns `ToolMessage` or
                `Command`.

        Returns:
            `ToolMessage` or `Command` (the final result).

        Raises:
            RuntimeError: If the retry loop completes without returning. This should not happen.
        """
        tool_name = request.tool.name if request.tool else request.tool_call["name"]

        # Check if retry should apply to this tool
        if not self._should_retry_tool(tool_name):
            return await handler(request)

        tool_call_id = request.tool_call["id"]

        # Initial attempt + retries
        for attempt in range(self.max_retries + 1):
            try:
                return await handler(request)
            except Exception as exc:
                attempts_made = attempt + 1  # attempt is 0-indexed

                # Check if we should retry this exception
                if not should_retry_exception(exc, self.retry_on):
                    # Exception is not retryable, handle failure immediately
                    return self._handle_failure(tool_name, tool_call_id, exc, attempts_made)

                # Check if we have more retries left
                if attempt < self.max_retries:
                    # Calculate and apply backoff delay
                    delay = calculate_delay(
                        attempt,
                        backoff_factor=self.backoff_factor,
                        initial_delay=self.initial_delay,
                        max_delay=self.max_delay,
                        jitter=self.jitter,
                    )
                    if delay > 0:
                        await asyncio.sleep(delay)
                    # Continue to next retry
                else:
                    # No more retries, handle failure
                    return self._handle_failure(tool_name, tool_call_id, exc, attempts_made)

        # Unreachable: loop always returns via handler success or _handle_failure
        msg = "Unexpected: retry loop completed without returning"
        raise RuntimeError(msg)