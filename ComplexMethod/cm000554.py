async def _execute_tools_agent_mode(
        self,
        input_data: "OrchestratorBlock.Input",
        credentials: llm.APIKeyCredentials,
        tool_functions: list[dict[str, Any]],
        prompt: list[dict[str, Any]],
        graph_exec_id: str,
        node_id: str,
        node_exec_id: str,
        user_id: str,
        graph_id: str,
        graph_version: int,
        execution_context: ExecutionContext,
        execution_processor: "ExecutionProcessor",
    ):
        """Execute tools in agent mode using the shared tool-calling loop."""
        max_iterations = input_data.agent_mode_max_iterations
        use_responses_api = input_data.model.metadata.provider == "openai"

        execution_params = ExecutionParams(
            user_id=user_id,
            graph_id=graph_id,
            node_id=node_id,
            graph_version=graph_version,
            graph_exec_id=graph_exec_id,
            node_exec_id=node_exec_id,
            execution_context=execution_context,
        )

        # Bind callbacks using functools.partial
        bound_llm_caller = partial(
            self._agent_mode_llm_caller,
            credentials=credentials,
            input_data=input_data,
        )
        bound_tool_executor = partial(
            self._agent_mode_tool_executor,
            execution_params=execution_params,
            execution_processor=execution_processor,
            use_responses_api=use_responses_api,
        )
        bound_conversation_updater = partial(
            self._agent_mode_conversation_updater,
            use_responses_api=use_responses_api,
        )

        current_prompt = list(prompt)

        last_iter_msg = None
        if max_iterations > 0:
            last_iter_msg = (
                f"{MAIN_OBJECTIVE_PREFIX}This is your last iteration. "
                "Try to complete the task with the information you have. "
                "If you cannot fully complete it, provide a summary of what "
                "you've accomplished and what remains to be done. "
                "Prefer finishing with a clear response rather than making "
                "additional tool calls."
            )

        try:
            loop_result = ToolCallLoopResult(response_text="", messages=current_prompt)
            async for loop_result in tool_call_loop(
                messages=current_prompt,
                tools=tool_functions,
                llm_call=bound_llm_caller,
                execute_tool=bound_tool_executor,
                update_conversation=bound_conversation_updater,
                max_iterations=max_iterations,
                last_iteration_message=last_iter_msg,
            ):
                # Yield intermediate tool calls so the UI can show progress.
                # Only yield conversations when there are tool calls to report;
                # the final conversation state is always emitted once after the
                # loop (line below) to avoid duplicate yields when max_iterations
                # is reached.
                if loop_result.last_tool_calls:
                    yield "conversations", loop_result.messages
                for tc in loop_result.last_tool_calls:
                    yield (
                        "tool_calls",
                        {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    )
        except InsufficientBalanceError:
            # IBE must propagate — see class docstring.
            raise
        except Exception as e:
            # Catch all OTHER errors (validation, network, API) so that
            # the block surfaces them as user-visible output instead of
            # crashing.
            yield "error", str(e)
            return

        if loop_result.finished_naturally:
            yield "finished", loop_result.response_text
        else:
            yield (
                "finished",
                (
                    f"Agent mode completed after {loop_result.iterations} "
                    "iterations (limit reached)"
                ),
            )
        yield "conversations", loop_result.messages