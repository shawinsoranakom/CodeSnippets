def _iter_next_step(
        self,
        name_to_tool_map: dict[str, BaseTool],
        color_mapping: dict[str, str],
        inputs: dict[str, str],
        intermediate_steps: list[tuple[AgentAction, str]],
        run_manager: CallbackManagerForChainRun | None = None,
    ) -> Iterator[AgentFinish | AgentAction | AgentStep]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the agent makes and acts on choices.
        """
        try:
            intermediate_steps = self._prepare_intermediate_steps(intermediate_steps)

            # Call the LLM to see what to do.
            output = self._action_agent.plan(
                intermediate_steps,
                callbacks=run_manager.get_child() if run_manager else None,
                **inputs,
            )
        except OutputParserException as e:
            if isinstance(self.handle_parsing_errors, bool):
                raise_error = not self.handle_parsing_errors
            else:
                raise_error = False
            if raise_error:
                msg = (
                    "An output parsing error occurred. "
                    "In order to pass this error back to the agent and have it try "
                    "again, pass `handle_parsing_errors=True` to the AgentExecutor. "
                    f"This is the error: {e!s}"
                )
                raise ValueError(msg) from e
            text = str(e)
            if isinstance(self.handle_parsing_errors, bool):
                if e.send_to_llm:
                    observation = str(e.observation)
                    text = str(e.llm_output)
                else:
                    observation = "Invalid or incomplete response"
            elif isinstance(self.handle_parsing_errors, str):
                observation = self.handle_parsing_errors
            elif callable(self.handle_parsing_errors):
                observation = self.handle_parsing_errors(e)
            else:
                msg = "Got unexpected type of `handle_parsing_errors`"  # type: ignore[unreachable]
                raise ValueError(msg) from e  # noqa: TRY004
            output = AgentAction("_Exception", observation, text)
            if run_manager:
                run_manager.on_agent_action(output, color="green")
            tool_run_kwargs = self._action_agent.tool_run_logging_kwargs()
            observation = ExceptionTool().run(
                output.tool_input,
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            yield AgentStep(action=output, observation=observation)
            return

        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, AgentFinish):
            yield output
            return

        actions: list[AgentAction]
        actions = [output] if isinstance(output, AgentAction) else output
        for agent_action in actions:
            yield agent_action
        for agent_action in actions:
            yield self._perform_agent_action(
                name_to_tool_map,
                color_mapping,
                agent_action,
                run_manager,
            )