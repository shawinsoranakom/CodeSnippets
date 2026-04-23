async def on_node_execution(
        self,
        node_exec: NodeExecutionEntry,
        node_exec_progress: NodeExecutionProgress,
        nodes_input_masks: Optional[NodesInputMasks],
        graph_stats_pair: tuple[GraphExecutionStats, threading.Lock],
        nodes_to_skip: Optional[set[str]] = None,
    ) -> NodeExecutionStats:
        log_metadata = LogMetadata(
            logger=_logger,
            user_id=node_exec.user_id,
            graph_eid=node_exec.graph_exec_id,
            graph_id=node_exec.graph_id,
            node_eid=node_exec.node_exec_id,
            node_id=node_exec.node_id,
            block_name=b.name if (b := get_block(node_exec.block_id)) else "-",
        )
        db_client = get_db_async_client()
        node = await db_client.get_node(node_exec.node_id)
        execution_stats = NodeExecutionStats()

        timing_info, status = await self._on_node_execution(
            node=node,
            node_exec=node_exec,
            node_exec_progress=node_exec_progress,
            stats=execution_stats,
            db_client=db_client,
            log_metadata=log_metadata,
            nodes_input_masks=nodes_input_masks,
            nodes_to_skip=nodes_to_skip,
        )
        if isinstance(status, BaseException):
            raise status

        execution_stats.walltime = timing_info.wall_time
        execution_stats.cputime = timing_info.cpu_time

        await billing.handle_post_execution_billing(
            node, node_exec, execution_stats, status, log_metadata
        )

        graph_stats, graph_stats_lock = graph_stats_pair
        with graph_stats_lock:
            graph_stats.node_count += 1 + execution_stats.extra_steps
            graph_stats.nodes_cputime += execution_stats.cputime
            graph_stats.nodes_walltime += execution_stats.walltime
            graph_stats.cost += execution_stats.cost + execution_stats.extra_cost
            if isinstance(execution_stats.error, Exception):
                graph_stats.node_error_count += 1

        node_error = execution_stats.error
        node_stats = execution_stats.model_dump()
        if node_error and not isinstance(node_error, str):
            node_stats["error"] = str(node_error) or node_stats.__class__.__name__

        await async_update_node_execution_status(
            db_client=db_client,
            exec_id=node_exec.node_exec_id,
            status=status,
            stats=node_stats,
        )
        await async_update_graph_execution_state(
            db_client=db_client,
            graph_exec_id=node_exec.graph_exec_id,
            stats=graph_stats,
        )

        # Log platform cost if system credentials were used (only on success)
        if status == ExecutionStatus.COMPLETED:
            await log_system_credential_cost(
                node_exec=node_exec,
                block=node.block,
                stats=execution_stats,
                db_client=db_client,
            )

        # If the node failed because a nested tool charge raised IBE,
        # send the user notification so they understand why the run stopped.
        if status == ExecutionStatus.FAILED and isinstance(
            execution_stats.error, InsufficientBalanceError
        ):
            await billing.try_send_insufficient_funds_notif(
                node_exec.user_id,
                node_exec.graph_id,
                execution_stats.error,
                log_metadata,
            )

        return execution_stats