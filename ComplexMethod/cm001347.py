async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:
        """Create a step for the task."""
        logger.debug(f"Creating a step for task with ID: {task_id}...")

        # Restore Agent instance
        task = await self.get_task(task_id)
        agent = configure_agent_with_state(
            state=self.agent_manager.load_agent_state(task_agent_id(task_id)),
            app_config=self.app_config,
            file_storage=self.file_storage,
            llm_provider=self._get_task_llm_provider(task),
        )

        if user_id := (task.additional_input or {}).get("user_id"):
            set_user({"id": user_id})

        # According to the Agent Protocol spec, the first execute_step request contains
        #  the same task input as the parent create_task request.
        # To prevent this from interfering with the agent's process, we ignore the input
        #  of this first step request, and just generate the first step proposal.
        is_init_step = not bool(agent.event_history)
        last_proposal, tool_result = None, None
        execute_approved = False

        # HACK: only for compatibility with AGBenchmark
        if step_request.input == "y":
            step_request.input = ""

        user_input = step_request.input if not is_init_step else ""

        if (
            not is_init_step
            and agent.event_history.current_episode
            and not agent.event_history.current_episode.result
        ):
            last_proposal = agent.event_history.current_episode.action
            execute_approved = not user_input

            logger.debug(
                f"Agent proposed command {last_proposal.use_tool}."
                f" User input/feedback: {repr(user_input)}"
            )

        # Save step request
        step = await self.db.create_step(
            task_id=task_id,
            input=step_request,
            is_last=(
                last_proposal is not None
                and last_proposal.use_tool.name == FINISH_COMMAND
                and execute_approved
            ),
        )
        agent.llm_provider = self._get_task_llm_provider(task, step.step_id)

        # Execute previously proposed action
        if last_proposal:
            agent.file_manager.workspace.on_write_file = (
                lambda path: self._on_agent_write_file(
                    task=task, step=step, relative_path=path
                )
            )

            if last_proposal.use_tool.name == ASK_COMMAND:
                tool_result = ActionSuccessResult(outputs=user_input)
                agent.event_history.register_result(tool_result)
            elif execute_approved:
                step = await self.db.update_step(
                    task_id=task_id,
                    step_id=step.step_id,
                    status="running",
                )

                try:
                    # Execute previously proposed action
                    tool_result = await agent.execute(last_proposal)
                except AgentFinished:
                    additional_output = {}
                    task_total_cost = agent.llm_provider.get_incurred_cost()
                    if task_total_cost > 0:
                        additional_output["task_total_cost"] = task_total_cost
                        logger.info(
                            f"Total LLM cost for task {task_id}: "
                            f"${round(task_total_cost, 2)}"
                        )

                    step = await self.db.update_step(
                        task_id=task_id,
                        step_id=step.step_id,
                        output=last_proposal.use_tool.arguments["reason"],
                        additional_output=additional_output,
                    )
                    await agent.file_manager.save_state()
                    return step
            else:
                assert user_input
                tool_result = await agent.do_not_execute(last_proposal, user_input)

        # Propose next action
        try:
            assistant_response = await agent.propose_action()
            next_tool_to_use = assistant_response.use_tool
            logger.debug(f"AI output: {assistant_response.thoughts}")
        except Exception as e:
            step = await self.db.update_step(
                task_id=task_id,
                step_id=step.step_id,
                status="completed",
                output=f"An error occurred while proposing the next action: {e}",
            )
            return step

        # Format step output
        output = (
            (
                f"`{last_proposal.use_tool}` returned:"
                + ("\n\n" if "\n" in str(tool_result) else " ")
                + f"{tool_result}\n\n"
            )
            if last_proposal and last_proposal.use_tool.name != ASK_COMMAND
            else ""
        )
        # Get thoughts summary or string representation
        thoughts = assistant_response.thoughts
        if isinstance(thoughts, str):
            thoughts_output = thoughts
        else:
            thoughts_output = thoughts.summary()
        output += f"{thoughts_output}\n\n"
        output += (
            f"Next Command: {next_tool_to_use}"
            if next_tool_to_use.name != ASK_COMMAND
            else next_tool_to_use.arguments["question"]
        )

        additional_output = {
            **(
                {
                    "last_action": {
                        "name": last_proposal.use_tool.name,
                        "args": last_proposal.use_tool.arguments,
                        "result": (
                            ""
                            if tool_result is None
                            else (
                                orjson.loads(tool_result.model_dump_json())
                                if not isinstance(tool_result, ActionErrorResult)
                                else {
                                    "error": str(tool_result.error),
                                    "reason": tool_result.reason,
                                }
                            )
                        ),
                    },
                }
                if last_proposal and tool_result
                else {}
            ),
            **assistant_response.model_dump(),
        }

        task_cumulative_cost = agent.llm_provider.get_incurred_cost()
        if task_cumulative_cost > 0:
            additional_output["task_cumulative_cost"] = task_cumulative_cost
        logger.debug(
            f"Running total LLM cost for task {task_id}: "
            f"${round(task_cumulative_cost, 3)}"
        )

        step = await self.db.update_step(
            task_id=task_id,
            step_id=step.step_id,
            status="completed",
            output=output,
            additional_output=additional_output,
        )

        await agent.file_manager.save_state()
        return step