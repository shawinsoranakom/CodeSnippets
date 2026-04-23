def _build_response(
        self,
        agent: LibraryAgent,
        execution: GraphExecution | GraphExecutionWithNodes | None,
        available_executions: list[GraphExecutionMeta],
        session_id: str | None,
    ) -> AgentOutputResponse:
        """Build the response based on execution data."""
        library_agent_link = f"/library/agents/{agent.id}"

        if not execution:
            return AgentOutputResponse(
                message=f"No completed executions found for agent '{agent.name}'",
                session_id=session_id,
                agent_name=agent.name,
                agent_id=agent.graph_id,
                library_agent_id=agent.id,
                library_agent_link=library_agent_link,
                total_executions=0,
            )

        node_executions_data = None
        if isinstance(execution, GraphExecutionWithNodes):
            node_executions_data = [
                {
                    "node_id": ne.node_id,
                    "block_id": ne.block_id,
                    "status": ne.status.value,
                    "input_data": ne.input_data,
                    "output_data": dict(ne.output_data),
                    "start_time": ne.start_time.isoformat() if ne.start_time else None,
                    "end_time": ne.end_time.isoformat() if ne.end_time else None,
                }
                for ne in execution.node_executions
            ]

        execution_info = ExecutionOutputInfo(
            execution_id=execution.id,
            status=execution.status.value,
            started_at=execution.started_at,
            ended_at=execution.ended_at,
            outputs=dict(execution.outputs),
            inputs_summary=execution.inputs if execution.inputs else None,
            node_executions=node_executions_data,
        )

        available_list = None
        if len(available_executions) > 1:
            available_list = [
                {
                    "id": e.id,
                    "status": e.status.value,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                }
                for e in available_executions[:5]
            ]

        # Build appropriate message based on execution status
        if execution.status == ExecutionStatus.COMPLETED:
            message = f"Found execution outputs for agent '{agent.name}'"
        elif execution.status == ExecutionStatus.FAILED:
            message = f"Execution for agent '{agent.name}' failed"
        elif execution.status == ExecutionStatus.TERMINATED:
            message = f"Execution for agent '{agent.name}' was terminated"
        elif execution.status == ExecutionStatus.REVIEW:
            message = (
                f"Execution for agent '{agent.name}' is awaiting human review. "
                "The user needs to approve it before it can continue."
            )
        elif execution.status in (
            ExecutionStatus.RUNNING,
            ExecutionStatus.QUEUED,
            ExecutionStatus.INCOMPLETE,
        ):
            message = (
                f"Execution for agent '{agent.name}' is still {execution.status.value}. "
                "Results may be incomplete. Use wait_if_running to wait for completion."
            )
        else:
            message = f"Found execution for agent '{agent.name}' (status: {execution.status.value})"

        if len(available_executions) > 1:
            message += (
                f" Showing latest of {len(available_executions)} matching executions."
            )

        return AgentOutputResponse(
            message=message,
            session_id=session_id,
            agent_name=agent.name,
            agent_id=agent.graph_id,
            library_agent_id=agent.id,
            library_agent_link=library_agent_link,
            execution=execution_info,
            available_executions=available_list,
            total_executions=len(available_executions) if available_executions else 1,
        )