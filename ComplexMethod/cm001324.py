async def execute(
        self,
        proposal: ActionProposal,
        user_feedback: str = "",
    ) -> ActionResult:
        # Get all tools to execute (supports parallel execution)
        tools = proposal.get_tools()

        # Get commands
        self.commands = await self.run_pipeline(CommandProvider.get_commands)
        self._remove_disabled_commands()

        # Check permissions for all tools before execution
        feedback_to_append = None
        if self.permission_manager:
            for tool in tools:
                perm_result = self.permission_manager.check_command(
                    tool.name, tool.arguments
                )
                if not perm_result.allowed:
                    # Permission denied - register as feedback so the agent
                    # knows to try a different approach instead of looping
                    feedback = (
                        perm_result.feedback
                        or f"Permission denied for command '{tool.name}'. "
                        "Try a different approach."
                    )
                    return await self.do_not_execute(proposal, feedback)
                # Permission granted - save feedback if any
                if perm_result.feedback:
                    feedback_to_append = perm_result.feedback

        # Execute tool(s)
        if len(tools) == 1:
            # Single tool - original behavior
            tool = tools[0]
            try:
                return_value = await self._execute_tool(tool)
                result = ActionSuccessResult(outputs=return_value)
            except AgentTerminated:
                raise
            except AgentException as e:
                result = ActionErrorResult.from_exception(e)
                logger.warning(f"{tool} raised an error: {e}")
                sentry_sdk.capture_exception(e)
        else:
            # Multiple tools - execute in parallel
            logger.info(f"Executing {len(tools)} tools in parallel")
            result = await self._execute_tools_parallel(tools)

        result_tlength = self.llm_provider.count_tokens(str(result), self.llm.name)
        if result_tlength > self.send_token_limit // 3:
            result = ActionErrorResult(
                reason="Command(s) returned too much output. "
                "Do not execute these commands again with the same arguments."
            )

        # Notify ReWOO strategy of execution result for variable tracking
        # This allows ReWOO to record results and substitute variables in later steps
        record_result = getattr(self.prompt_strategy, "record_execution_result", None)
        plan = getattr(self.prompt_strategy, "current_plan", None)
        if record_result is not None and plan is not None:
            if plan.current_step_index < len(plan.steps):
                step = plan.steps[plan.current_step_index]
                error_msg = None
                if isinstance(result, ActionErrorResult):
                    error_msg = getattr(result, "reason", None) or str(result)
                result_str = str(getattr(result, "outputs", result))
                record_result(
                    step.variable_name,
                    result_str,
                    error=error_msg,
                )
                logger.debug(
                    f"ReWOO: Recorded result for {step.variable_name}, "
                    f"step {plan.current_step_index + 1}/{len(plan.steps)}"
                )

        await self.run_pipeline(AfterExecute.after_execute, result)

        # If user provided feedback along with approval, append it to history
        # so the agent sees it in the next iteration
        if feedback_to_append:
            self.event_history.append_user_feedback(feedback_to_append)

        logger.debug("\n".join(self.trace))

        return result