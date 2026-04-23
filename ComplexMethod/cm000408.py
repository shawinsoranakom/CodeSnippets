async def _update_failed_nodes_for_moderation(
        self,
        db_client: "DatabaseManagerAsyncClient",
        graph_exec_id: str,
        moderation_type: Literal["input", "output"],
        content_id: str | None = None,
    ):
        """Update node execution statuses for frontend display when moderation fails"""
        # Import here to avoid circular imports
        from backend.executor.manager import send_async_execution_update

        if moderation_type == "input":
            # For input moderation, mark queued/running/incomplete nodes as failed
            target_statuses = [
                ExecutionStatus.QUEUED,
                ExecutionStatus.RUNNING,
                ExecutionStatus.INCOMPLETE,
            ]
        else:
            # For output moderation, mark completed nodes as failed
            target_statuses = [ExecutionStatus.COMPLETED]

        # Get the executions that need to be updated
        executions_to_update = await db_client.get_node_executions(
            graph_exec_id, statuses=target_statuses, include_exec_data=True
        )

        if not executions_to_update:
            return

        # Create error message with content_id if available
        error_message = "Failed due to content moderation"
        if content_id:
            error_message += f" (Moderation ID: {content_id})"

        # Prepare database update tasks
        exec_updates = []
        for exec_entry in executions_to_update:
            # Collect all input and output names to clear
            cleared_inputs = {}
            cleared_outputs = {}

            if exec_entry.input_data:
                for name in exec_entry.input_data.keys():
                    cleared_inputs[name] = [error_message]

            if exec_entry.output_data:
                for name in exec_entry.output_data.keys():
                    cleared_outputs[name] = [error_message]

            # Add update task to list
            exec_updates.append(
                db_client.update_node_execution_status(
                    exec_entry.node_exec_id,
                    status=ExecutionStatus.FAILED,
                    stats={
                        "error": error_message,
                        "cleared_inputs": cleared_inputs,
                        "cleared_outputs": cleared_outputs,
                    },
                )
            )

        # Execute all database updates in parallel
        updated_execs = await asyncio.gather(*exec_updates)

        # Send all websocket updates in parallel
        await asyncio.gather(
            *[
                send_async_execution_update(updated_exec)
                for updated_exec in updated_execs
            ]
        )