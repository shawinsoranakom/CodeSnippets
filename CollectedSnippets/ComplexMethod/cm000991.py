async def _run_agent(
        self,
        user_id: str,
        session: ChatSession,
        graph: GraphModel,
        graph_credentials: dict[str, CredentialsMetaInput],
        inputs: dict[str, Any],
        dry_run: bool,
        wait_for_result: int = 0,
    ) -> ToolResponseBase:
        """Execute an agent immediately, optionally waiting for completion."""
        session_id = session.session_id

        # Check rate limits (dry runs don't count against the session limit)
        if (
            not dry_run
            and session.successful_agent_runs.get(graph.id, 0) >= config.max_agent_runs
        ):
            return ErrorResponse(
                message="Maximum agent runs reached for this session. Please try again later.",
                session_id=session_id,
            )

        # Get or create library agent
        library_agent = await get_or_create_library_agent(graph, user_id)

        # Execute — ``add_graph_execution`` ultimately calls
        # ``validate_and_construct_node_execution_input`` which raises
        # ``GraphValidationError`` on missing/invalid credentials.  The
        # common case is caught by ``_check_prerequisites`` above, but
        # defend against a race (creds deleted between prereq and
        # execute) by turning credential errors back into the inline
        # setup card.
        try:
            execution = await execution_utils.add_graph_execution(
                graph_id=library_agent.graph_id,
                user_id=user_id,
                inputs=inputs,
                graph_credentials_inputs=graph_credentials,
                dry_run=dry_run,
            )
        except GraphValidationError as e:
            return self._handle_graph_validation_race(
                error=e,
                graph=graph,
                user_id=user_id,
                session_id=session_id,
                action_verb="running",
            )

        # Track successful run (dry runs don't count against the session limit)
        if not dry_run:
            session.successful_agent_runs[library_agent.graph_id] = (
                session.successful_agent_runs.get(library_agent.graph_id, 0) + 1
            )

        # Track in PostHog
        track_agent_run_success(
            user_id=user_id,
            session_id=session_id,
            graph_id=library_agent.graph_id,
            graph_name=library_agent.name,
            execution_id=execution.id,
            library_agent_id=library_agent.id,
        )

        library_agent_link = f"/library/agents/{library_agent.id}"

        # If wait_for_result is requested, wait for execution to complete
        if wait_for_result > 0:
            logger.info(
                f"Waiting up to {wait_for_result}s for execution {execution.id}"
            )
            completed = await wait_for_execution(
                user_id=user_id,
                graph_id=library_agent.graph_id,
                execution_id=execution.id,
                timeout_seconds=wait_for_result,
            )

            if completed and completed.status == ExecutionStatus.COMPLETED:
                outputs = get_execution_outputs(completed)
                # Inline the per-node execution trace on dry-runs so the
                # LLM can inspect "did every block run, what did each
                # produce?" without a follow-up view_agent_output call.
                # Empty final outputs on a COMPLETED dry-run almost always
                # mean a node silently produced nothing / a link was wired
                # wrong — the trace is what lets the model debug that.
                node_executions_data = None
                if dry_run:
                    try:
                        detailed = await execution_db().get_graph_execution(
                            user_id=user_id,
                            execution_id=execution.id,
                            include_node_executions=True,
                        )
                        if isinstance(detailed, GraphExecutionWithNodes):
                            node_executions_data = [
                                {
                                    "node_id": ne.node_id,
                                    "block_id": ne.block_id,
                                    "status": ne.status.value,
                                    "input_data": ne.input_data,
                                    "output_data": dict(ne.output_data),
                                    "start_time": (
                                        ne.start_time.isoformat()
                                        if ne.start_time
                                        else None
                                    ),
                                    "end_time": (
                                        ne.end_time.isoformat() if ne.end_time else None
                                    ),
                                }
                                for ne in detailed.node_executions
                            ]
                    except Exception:
                        logger.warning(
                            "run_agent: failed to load node executions for "
                            "dry-run %s; returning summary only",
                            execution.id,
                            exc_info=True,
                        )
                return AgentOutputResponse(
                    message=(
                        f"Agent '{library_agent.name}' completed successfully. "
                        f"View at {library_agent_link}."
                    ),
                    session_id=session_id,
                    agent_name=library_agent.name,
                    agent_id=library_agent.graph_id,
                    library_agent_id=library_agent.id,
                    library_agent_link=library_agent_link,
                    execution=ExecutionOutputInfo(
                        execution_id=execution.id,
                        status=completed.status.value,
                        started_at=completed.started_at,
                        ended_at=completed.ended_at,
                        outputs=outputs or {},
                        node_executions=node_executions_data,
                    ),
                )
            elif completed and completed.status == ExecutionStatus.FAILED:
                error_detail = completed.stats.error if completed.stats else None
                return ErrorResponse(
                    message=(
                        f"Agent '{library_agent.name}' execution failed. "
                        f"View details at {library_agent_link}."
                    ),
                    session_id=session_id,
                    error=error_detail,
                )
            elif completed and completed.status == ExecutionStatus.TERMINATED:
                error_detail = completed.stats.error if completed.stats else None
                return ErrorResponse(
                    message=(
                        f"Agent '{library_agent.name}' execution was terminated. "
                        f"View details at {library_agent_link}."
                    ),
                    session_id=session_id,
                    error=error_detail,
                )
            elif completed and completed.status == ExecutionStatus.REVIEW:
                return ExecutionStartedResponse(
                    message=(
                        f"Agent '{library_agent.name}' is awaiting human review. "
                        f"The user can approve or reject inline. After approval, "
                        f"the execution resumes automatically. Use view_agent_output "
                        f"with execution_id='{execution.id}' to check the result."
                    ),
                    session_id=session_id,
                    execution_id=execution.id,
                    graph_id=library_agent.graph_id,
                    graph_name=library_agent.name,
                    library_agent_id=library_agent.id,
                    library_agent_link=library_agent_link,
                    status=ExecutionStatus.REVIEW.value,
                )
            else:
                status = completed.status.value if completed else "unknown"
                return ExecutionStartedResponse(
                    message=(
                        f"Agent '{library_agent.name}' is still {status} after "
                        f"{wait_for_result}s. Check results later at "
                        f"{library_agent_link}. "
                        f"Use view_agent_output with wait_if_running to check again."
                    ),
                    session_id=session_id,
                    execution_id=execution.id,
                    graph_id=library_agent.graph_id,
                    graph_name=library_agent.name,
                    library_agent_id=library_agent.id,
                    library_agent_link=library_agent_link,
                    status=status,
                )

        return ExecutionStartedResponse(
            message=(
                f"Agent '{library_agent.name}' execution started successfully. "
                f"View at {library_agent_link}. "
                f"{MSG_DO_NOT_RUN_AGAIN}"
            ),
            session_id=session_id,
            execution_id=execution.id,
            graph_id=library_agent.graph_id,
            graph_name=library_agent.name,
            library_agent_id=library_agent.id,
            library_agent_link=library_agent_link,
        )