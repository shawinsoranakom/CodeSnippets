async def _acall(
        self,
        inputs: dict[str, str],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, str]:
        """Async run text through and get agent response."""
        # Construct a mapping of tool name to tool for easy lookup
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        # We construct a mapping from each tool to a color, used for logging.
        color_mapping = get_color_mapping(
            [tool.name for tool in self.tools],
            excluded_colors=["green"],
        )
        intermediate_steps: list[tuple[AgentAction, str]] = []
        # Let's start tracking the number of iterations and time elapsed
        iterations = 0
        time_elapsed = 0.0
        start_time = time.time()
        # We now enter the agent loop (until it returns something).
        try:
            async with asyncio_timeout(self.max_execution_time):
                while self._should_continue(iterations, time_elapsed):
                    next_step_output = await self._atake_next_step(
                        name_to_tool_map,
                        color_mapping,
                        inputs,
                        intermediate_steps,
                        run_manager=run_manager,
                    )
                    if isinstance(next_step_output, AgentFinish):
                        return await self._areturn(
                            next_step_output,
                            intermediate_steps,
                            run_manager=run_manager,
                        )

                    intermediate_steps.extend(next_step_output)
                    if len(next_step_output) == 1:
                        next_step_action = next_step_output[0]
                        # See if tool should return directly
                        tool_return = self._get_tool_return(next_step_action)
                        if tool_return is not None:
                            return await self._areturn(
                                tool_return,
                                intermediate_steps,
                                run_manager=run_manager,
                            )

                    iterations += 1
                    time_elapsed = time.time() - start_time
                output = self._action_agent.return_stopped_response(
                    self.early_stopping_method,
                    intermediate_steps,
                    **inputs,
                )
                return await self._areturn(
                    output,
                    intermediate_steps,
                    run_manager=run_manager,
                )
        except (TimeoutError, asyncio.TimeoutError):
            # stop early when interrupted by the async timeout
            output = self._action_agent.return_stopped_response(
                self.early_stopping_method,
                intermediate_steps,
                **inputs,
            )
            return await self._areturn(
                output,
                intermediate_steps,
                run_manager=run_manager,
            )