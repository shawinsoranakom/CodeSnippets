async def _execute_tools_parallel(
        self, tools: list[AssistantFunctionCall]
    ) -> ActionResult:
        """Execute multiple tools in parallel and combine results.

        Args:
            tools: List of tool calls to execute in parallel

        Returns:
            Combined ActionResult with all outputs or errors
        """

        async def execute_single(tool: AssistantFunctionCall) -> tuple[str, Any, str]:
            """Execute a single tool and return (name, result, error)."""
            try:
                result = await self._execute_tool(tool)
                return (tool.name, result, "")
            except AgentTerminated:
                raise
            except AgentException as e:
                logger.warning(f"{tool} raised an error: {e}")
                sentry_sdk.capture_exception(e)
                return (tool.name, None, str(e))

        # Execute all tools in parallel
        results = await asyncio.gather(
            *[execute_single(tool) for tool in tools],
            return_exceptions=True,
        )

        # Process results
        outputs: dict[str, Any] = {}
        errors: list[str] = []

        for i, res in enumerate(results):
            tool = tools[i]
            if isinstance(res, BaseException):
                # Unexpected exception from gather
                errors.append(f"{tool.name}: {res}")
                logger.warning(f"{tool} raised unexpected error: {res}")
                sentry_sdk.capture_exception(res)
            elif isinstance(res, tuple):
                name, output, error = res
                if error:
                    errors.append(f"{name}: {error}")
                else:
                    outputs[name] = output

        # Return combined result
        if errors and not outputs:
            # All failed
            return ActionErrorResult(reason="; ".join(errors))
        elif errors:
            # Partial success - include errors in output
            outputs["_errors"] = errors
            return ActionSuccessResult(outputs=outputs)
        else:
            # All succeeded
            return ActionSuccessResult(outputs=outputs)