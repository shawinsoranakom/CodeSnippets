async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        **kwargs,
    ) -> ToolResponseBase:
        """Execute the tool with automatic state detection.

        Note: This tool accepts **kwargs and delegates to RunAgentInput for
        validation because the parameter set is complex with cross-field
        validators defined in the Pydantic model.
        """
        params = RunAgentInput(**kwargs)
        # Session-level dry_run forces all runs to be dry. In normal sessions
        # the LLM may still request dry_run=True on individual calls.
        if session.dry_run:
            params.dry_run = True
        session_id = session.session_id

        # Validate at least one identifier is provided
        has_slug = params.username_agent_slug and "/" in params.username_agent_slug
        has_library_id = bool(params.library_agent_id)

        # Builder-bound sessions can omit the identifier — default to the
        # bound graph so the LLM doesn't have to pass IDs the user never sees.
        builder_graph_id = session.metadata.builder_graph_id
        if builder_graph_id and user_id and not has_slug and not has_library_id:
            library_agent = await library_db().get_library_agent_by_graph_id(
                user_id, builder_graph_id
            )
            if library_agent:
                params.library_agent_id = library_agent.id
                has_library_id = True

        if not has_slug and not has_library_id:
            return ErrorResponse(
                message=(
                    "Please provide either a username_agent_slug "
                    "(format 'username/agent-name') or a library_agent_id"
                ),
                session_id=session_id,
            )

        # Auth is required
        if not user_id:
            return ErrorResponse(
                message="Authentication required. Please sign in to use this tool.",
                session_id=session_id,
            )

        # Determine if this is a schedule request
        is_schedule = bool(params.schedule_name or params.cron)

        # Session-level dry-run blocks scheduling — schedules create real
        # side effects that cannot be simulated.
        if params.dry_run and is_schedule:
            return ErrorResponse(
                message=(
                    "Scheduling is disabled in dry-run mode because it creates "
                    "real side effects. Remove cron/schedule_name to simulate "
                    "a run, or disable dry-run to create a real schedule."
                ),
                session_id=session_id,
            )

        try:
            # Step 1: Fetch agent details
            graph: GraphModel | None = None
            library_agent = None

            # Priority: library_agent_id if provided
            if has_library_id:
                library_agent = await library_db().get_library_agent(
                    params.library_agent_id, user_id
                )
                if not library_agent:
                    return ErrorResponse(
                        message=f"Library agent '{params.library_agent_id}' not found",
                        session_id=session_id,
                    )
                # Get the graph from the library agent
                graph = await graph_db().get_graph(
                    library_agent.graph_id,
                    library_agent.graph_version,
                    user_id=user_id,
                )
            else:
                # Fetch from marketplace slug
                username, agent_name = params.username_agent_slug.split("/", 1)
                graph, _ = await fetch_graph_from_store_slug(username, agent_name)

            if not graph:
                identifier = (
                    params.library_agent_id
                    if has_library_id
                    else params.username_agent_slug
                )
                return ErrorResponse(
                    message=f"Agent '{identifier}' not found",
                    session_id=session_id,
                )

            # Builder-bound sessions can only run their bound agent.  We
            # resolve the graph first so the user sees a precise error that
            # references the agent they actually asked to run, rather than
            # pre-emptively rejecting every run request.
            if builder_graph_id and graph.id != builder_graph_id:
                return ErrorResponse(
                    message=(
                        "This chat is bound to the builder's current agent. "
                        "Running a different agent is not allowed here."
                    ),
                    error="builder_session_graph_mismatch",
                    session_id=session_id,
                )

            # Step 2: Check credentials and inputs
            graph_credentials, prereq_error = await self._check_prerequisites(
                graph=graph,
                user_id=user_id,
                params=params,
                session_id=session_id,
            )
            if prereq_error:
                return prereq_error

            # Step 3: Execute or Schedule
            if is_schedule:
                return await self._schedule_agent(
                    user_id=user_id,
                    session=session,
                    graph=graph,
                    graph_credentials=graph_credentials,
                    inputs=params.inputs,
                    schedule_name=params.schedule_name,
                    cron=params.cron,
                    timezone=params.timezone,
                )
            else:
                return await self._run_agent(
                    user_id=user_id,
                    session=session,
                    graph=graph,
                    graph_credentials=graph_credentials,
                    inputs=params.inputs,
                    wait_for_result=params.wait_for_result,
                    dry_run=params.dry_run,
                )

        except NotFoundError as e:
            return ErrorResponse(
                message=f"Agent '{params.username_agent_slug}' not found",
                error=str(e) if str(e) else "not_found",
                session_id=session_id,
            )
        except DatabaseError as e:
            logger.error("Database error: %s", e, exc_info=True)
            return ErrorResponse(
                message=f"Failed to process request: {e!s}",
                error=str(e),
                session_id=session_id,
            )
        except Exception as e:
            logger.error("Error processing agent request: %s", e, exc_info=True)
            return ErrorResponse(
                message=f"Failed to process request: {e!s}",
                error=str(e),
                session_id=session_id,
            )