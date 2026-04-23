async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        **kwargs,
    ) -> ToolResponseBase:
        """Execute the agent_output tool.

        Note: This tool accepts **kwargs and delegates to AgentOutputInput
        for validation because the parameter set has cross-field validators
        defined in the Pydantic model.
        """
        session_id = session.session_id

        # Parse and validate input
        try:
            input_data = AgentOutputInput(**kwargs)
        except Exception as e:
            logger.error(f"Invalid input: {e}")
            return ErrorResponse(
                message="Invalid input parameters",
                error=str(e),
                session_id=session_id,
            )

        # Ensure user_id is present (should be guaranteed by requires_auth)
        if not user_id:
            return ErrorResponse(
                message="User authentication required",
                session_id=session_id,
            )

        # Check if at least one identifier is provided
        if not any(
            [
                input_data.agent_name,
                input_data.library_agent_id,
                input_data.store_slug,
                input_data.execution_id,
            ]
        ):
            return ErrorResponse(
                message=(
                    "Please specify at least one of: agent_name, "
                    "library_agent_id, store_slug, or execution_id"
                ),
                session_id=session_id,
            )

        # If only execution_id provided, we need to find the agent differently
        if (
            input_data.execution_id
            and not input_data.agent_name
            and not input_data.library_agent_id
            and not input_data.store_slug
        ):
            # Fetch execution directly to get graph_id
            execution = await execution_db().get_graph_execution(
                user_id=user_id,
                execution_id=input_data.execution_id,
                include_node_executions=input_data.show_execution_details,
            )
            if not execution:
                return ErrorResponse(
                    message=f"Execution '{input_data.execution_id}' not found",
                    session_id=session_id,
                )

            # Find library agent by graph_id
            agent = await library_db().get_library_agent_by_graph_id(
                user_id, execution.graph_id
            )
            if not agent:
                return NoResultsResponse(
                    message=(
                        f"Execution found but agent not in your library. "
                        f"Graph ID: {execution.graph_id}"
                    ),
                    session_id=session_id,
                    suggestions=["Add the agent to your library to see more details"],
                )

            return self._build_response(agent, execution, [], session_id)

        # Resolve agent from identifiers
        agent, error = await self._resolve_agent(
            user_id=user_id,
            agent_name=input_data.agent_name or None,
            library_agent_id=input_data.library_agent_id or None,
            store_slug=input_data.store_slug or None,
        )

        if error or not agent:
            return NoResultsResponse(
                message=error or "Agent not found",
                session_id=session_id,
                suggestions=[
                    "Check the agent name or ID",
                    "Make sure the agent is in your library",
                ],
            )

        # Parse time expression
        time_start, time_end = parse_time_expression(input_data.run_time)

        # Check if we should wait for running executions
        wait_timeout = input_data.wait_if_running

        # Fetch execution(s) - include running if we're going to wait
        execution, available_executions, exec_error = await self._get_execution(
            user_id=user_id,
            graph_id=agent.graph_id,
            execution_id=input_data.execution_id or None,
            time_start=time_start,
            time_end=time_end,
            include_running=wait_timeout > 0,
            include_node_executions=input_data.show_execution_details,
        )

        if exec_error:
            return ErrorResponse(
                message=exec_error,
                session_id=session_id,
            )

        # If we have an execution that's still running and we should wait
        if execution and wait_timeout > 0 and execution.status not in TERMINAL_STATUSES:
            logger.info(
                f"Execution {execution.id} is {execution.status}, "
                f"waiting up to {wait_timeout}s for completion"
            )
            execution = await wait_for_execution(
                user_id=user_id,
                graph_id=agent.graph_id,
                execution_id=execution.id,
                timeout_seconds=wait_timeout,
            )

        return self._build_response(agent, execution, available_executions, session_id)