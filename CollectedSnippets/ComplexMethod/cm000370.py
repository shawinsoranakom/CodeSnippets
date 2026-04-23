def on_graph_execution(
        self,
        graph_exec: GraphExecutionEntry,
        cancel: threading.Event,
        cluster_lock: ClusterLock,
    ):
        log_metadata = LogMetadata(
            logger=_logger,
            user_id=graph_exec.user_id,
            graph_eid=graph_exec.graph_exec_id,
            graph_id=graph_exec.graph_id,
            node_id="*",
            node_eid="*",
            block_name="-",
        )
        db_client = get_db_client()

        exec_meta = db_client.get_graph_execution_meta(
            user_id=graph_exec.user_id,
            execution_id=graph_exec.graph_exec_id,
        )
        if exec_meta is None:
            log_metadata.warning(
                f"Skipped graph execution #{graph_exec.graph_exec_id}, the graph execution is not found."
            )
            return

        if exec_meta.status in [ExecutionStatus.QUEUED, ExecutionStatus.INCOMPLETE]:
            log_metadata.info(f"⚙️ Starting graph execution #{graph_exec.graph_exec_id}")
            exec_meta.status = ExecutionStatus.RUNNING
            send_execution_update(
                db_client.update_graph_execution_start_time(graph_exec.graph_exec_id)
            )
        elif exec_meta.status == ExecutionStatus.RUNNING:
            log_metadata.info(
                f"⚙️ Graph execution #{graph_exec.graph_exec_id} is already running, continuing where it left off."
            )
        elif exec_meta.status == ExecutionStatus.REVIEW:
            exec_meta.status = ExecutionStatus.RUNNING
            log_metadata.info(
                f"⚙️ Graph execution #{graph_exec.graph_exec_id} was waiting for review, resuming execution."
            )
            update_graph_execution_state(
                db_client=db_client,
                graph_exec_id=graph_exec.graph_exec_id,
                status=ExecutionStatus.RUNNING,
            )
        elif exec_meta.status == ExecutionStatus.FAILED:
            exec_meta.status = ExecutionStatus.RUNNING
            log_metadata.info(
                f"⚙️ Graph execution #{graph_exec.graph_exec_id} was disturbed, continuing where it left off."
            )
            update_graph_execution_state(
                db_client=db_client,
                graph_exec_id=graph_exec.graph_exec_id,
                status=ExecutionStatus.RUNNING,
            )
        else:
            log_metadata.warning(
                f"Skipped graph execution {graph_exec.graph_exec_id}, the graph execution status is `{exec_meta.status}`."
            )
            return

        if exec_meta.stats is None:
            exec_stats = GraphExecutionStats(
                is_dry_run=graph_exec.execution_context.dry_run,
            )
        else:
            exec_stats = exec_meta.stats.to_db()
            exec_stats.is_dry_run = graph_exec.execution_context.dry_run

        timing_info, status = self._on_graph_execution(
            graph_exec=graph_exec,
            cancel=cancel,
            log_metadata=log_metadata,
            execution_stats=exec_stats,
            cluster_lock=cluster_lock,
        )
        exec_stats.walltime += timing_info.wall_time
        exec_stats.cputime += timing_info.cpu_time

        try:
            # Failure handling
            if isinstance(status, BaseException):
                raise status
            exec_meta.status = status

            if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
                activity_response = asyncio.run_coroutine_threadsafe(
                    generate_activity_status_for_execution(
                        graph_exec_id=graph_exec.graph_exec_id,
                        graph_id=graph_exec.graph_id,
                        graph_version=graph_exec.graph_version,
                        execution_stats=exec_stats,
                        db_client=get_db_async_client(),
                        user_id=graph_exec.user_id,
                        execution_status=status,
                    ),
                    self.node_execution_loop,
                ).result(timeout=60.0)
            else:
                activity_response = None
            if activity_response is not None:
                exec_stats.activity_status = activity_response["activity_status"]
                exec_stats.correctness_score = activity_response["correctness_score"]
                log_metadata.info(
                    f"Generated activity status: {activity_response['activity_status']} "
                    f"(correctness: {activity_response['correctness_score']:.2f})"
                )
            else:
                log_metadata.debug(
                    "Activity status generation disabled, not setting fields"
                )
        finally:
            # Communication handling
            billing.handle_agent_run_notif(db_client, graph_exec, exec_stats)

            update_graph_execution_state(
                db_client=db_client,
                graph_exec_id=graph_exec.graph_exec_id,
                status=exec_meta.status,
                stats=exec_stats,
            )