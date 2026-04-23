def _cleanup_graph_execution(
        self,
        execution_queue: ExecutionQueue[NodeExecutionEntry],
        running_node_execution: dict[str, "NodeExecutionProgress"],
        running_node_evaluation: dict[str, Future],
        execution_status: ExecutionStatus,
        error: Exception | None,
        graph_exec_id: str,
        log_metadata: LogMetadata,
        db_client: "DatabaseManagerClient",
    ) -> None:
        """
        Clean up running node executions and evaluations when graph execution ends.
        This method is decorated with @error_logged(swallow=True) to ensure cleanup
        never fails in the finally block.
        """
        # Cancel and wait for all node executions to complete
        for node_id, inflight_exec in running_node_execution.items():
            if inflight_exec.is_done():
                continue
            log_metadata.info(f"Stopping node execution {node_id}")
            inflight_exec.stop()

        for node_id, inflight_exec in running_node_execution.items():
            try:
                inflight_exec.wait_for_done(timeout=3600.0)
            except TimeoutError:
                log_metadata.exception(
                    f"Node execution #{node_id} did not stop in time, "
                    "it may be stuck or taking too long."
                )

        # Wait the remaining inflight evaluations to finish
        for node_id, inflight_eval in running_node_evaluation.items():
            try:
                inflight_eval.result(timeout=3600.0)
            except TimeoutError:
                log_metadata.exception(
                    f"Node evaluation #{node_id} did not stop in time, "
                    "it may be stuck or taking too long."
                )

        while queued_execution := execution_queue.get_or_none():
            update_node_execution_status(
                db_client=db_client,
                exec_id=queued_execution.node_exec_id,
                status=execution_status,
                stats={"error": str(error)} if error else None,
            )

        clean_exec_files(graph_exec_id)