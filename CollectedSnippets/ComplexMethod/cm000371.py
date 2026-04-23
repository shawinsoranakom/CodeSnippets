def _on_graph_execution(
        self,
        graph_exec: GraphExecutionEntry,
        cancel: threading.Event,
        log_metadata: LogMetadata,
        execution_stats: GraphExecutionStats,
        cluster_lock: ClusterLock,
    ) -> ExecutionStatus:
        """
        Returns:
            dict: The execution statistics of the graph execution.
            ExecutionStatus: The final status of the graph execution.
            Exception | None: The error that occurred during the execution, if any.
        """
        execution_status: ExecutionStatus = ExecutionStatus.RUNNING
        error: Exception | None = None
        db_client = get_db_client()
        execution_stats_lock = threading.Lock()

        # State holders ----------------------------------------------------
        self.running_node_execution: dict[str, NodeExecutionProgress] = defaultdict(
            NodeExecutionProgress
        )
        self.running_node_evaluation: dict[str, Future] = {}
        self.execution_stats = execution_stats
        self.execution_stats_lock = execution_stats_lock
        execution_queue = ExecutionQueue[NodeExecutionEntry]()

        running_node_execution = self.running_node_execution
        running_node_evaluation = self.running_node_evaluation

        try:
            if (
                not graph_exec.execution_context.dry_run
                and db_client.get_credits(graph_exec.user_id) <= 0
            ):
                raise InsufficientBalanceError(
                    user_id=graph_exec.user_id,
                    message="You have no credits left to run an agent.",
                    balance=0,
                    amount=1,
                )

            # Input moderation
            try:
                if moderation_error := asyncio.run_coroutine_threadsafe(
                    automod_manager.moderate_graph_execution_inputs(
                        db_client=get_db_async_client(),
                        graph_exec=graph_exec,
                    ),
                    self.node_evaluation_loop,
                ).result(timeout=30.0):
                    raise moderation_error
            except asyncio.TimeoutError:
                log_metadata.warning(
                    f"Input moderation timed out for graph execution {graph_exec.graph_exec_id}, bypassing moderation and continuing execution"
                )
                # Continue execution without moderation

            # ------------------------------------------------------------
            # Pre‑populate queue ---------------------------------------
            # ------------------------------------------------------------
            for node_exec in db_client.get_node_executions(
                graph_exec.graph_exec_id,
                statuses=[
                    ExecutionStatus.RUNNING,
                    ExecutionStatus.QUEUED,
                    ExecutionStatus.TERMINATED,
                    ExecutionStatus.REVIEW,
                ],
            ):
                node_entry = node_exec.to_node_execution_entry(
                    graph_exec.execution_context
                )
                execution_queue.add(node_entry)

            # ------------------------------------------------------------
            # Main dispatch / polling loop -----------------------------
            # ------------------------------------------------------------

            while not execution_queue.empty():
                if cancel.is_set():
                    break

                queued_node_exec = execution_queue.get()

                # Check if this node should be skipped due to optional credentials
                if queued_node_exec.node_id in graph_exec.nodes_to_skip:
                    log_metadata.info(
                        f"Skipping node execution {queued_node_exec.node_exec_id} "
                        f"for node {queued_node_exec.node_id} - optional credentials not configured"
                    )
                    # Mark the node as completed without executing
                    # No outputs will be produced, so downstream nodes won't trigger
                    update_node_execution_status(
                        db_client=db_client,
                        exec_id=queued_node_exec.node_exec_id,
                        status=ExecutionStatus.COMPLETED,
                    )
                    continue

                log_metadata.debug(
                    f"Dispatching node execution {queued_node_exec.node_exec_id} "
                    f"for node {queued_node_exec.node_id}",
                )

                # Charge usage (may raise) — skipped for dry runs
                try:
                    if not graph_exec.execution_context.dry_run:
                        cost, remaining_balance = billing.charge_usage(
                            node_exec=queued_node_exec,
                            execution_count=increment_execution_count(
                                graph_exec.user_id
                            ),
                        )
                        with execution_stats_lock:
                            execution_stats.cost += cost
                        # Check if we crossed the low balance threshold
                        billing.handle_low_balance(
                            db_client=db_client,
                            user_id=graph_exec.user_id,
                            current_balance=remaining_balance,
                            transaction_cost=cost,
                        )
                except InsufficientBalanceError as balance_error:
                    error = balance_error  # Set error to trigger FAILED status
                    node_exec_id = queued_node_exec.node_exec_id
                    db_client.upsert_execution_output(
                        node_exec_id=node_exec_id,
                        output_name="error",
                        output_data=str(error),
                    )
                    update_node_execution_status(
                        db_client=db_client,
                        exec_id=node_exec_id,
                        status=ExecutionStatus.FAILED,
                    )

                    billing.handle_insufficient_funds_notif(
                        db_client,
                        graph_exec.user_id,
                        graph_exec.graph_id,
                        error,
                    )
                    # Gracefully stop the execution loop
                    break

                # Add input overrides -----------------------------
                node_id = queued_node_exec.node_id
                if (nodes_input_masks := graph_exec.nodes_input_masks) and (
                    node_input_mask := nodes_input_masks.get(node_id)
                ):
                    queued_node_exec.inputs.update(node_input_mask)

                # Kick off async node execution -------------------------
                node_execution_task = asyncio.run_coroutine_threadsafe(
                    self.on_node_execution(
                        node_exec=queued_node_exec,
                        node_exec_progress=running_node_execution[node_id],
                        nodes_input_masks=nodes_input_masks,
                        graph_stats_pair=(
                            execution_stats,
                            execution_stats_lock,
                        ),
                        nodes_to_skip=graph_exec.nodes_to_skip,
                    ),
                    self.node_execution_loop,
                )
                running_node_execution[node_id].add_task(
                    node_exec_id=queued_node_exec.node_exec_id,
                    task=node_execution_task,
                )

                # Poll until queue refills or all inflight work done ----
                while execution_queue.empty() and (
                    running_node_execution or running_node_evaluation
                ):
                    if cancel.is_set():
                        break

                    # --------------------------------------------------
                    # Handle inflight evaluations ---------------------
                    # --------------------------------------------------
                    node_output_found = False
                    for node_id, inflight_exec in list(running_node_execution.items()):
                        if cancel.is_set():
                            break

                        # node evaluation future -----------------
                        if inflight_eval := running_node_evaluation.get(node_id):
                            if not inflight_eval.done():
                                continue
                            try:
                                inflight_eval.result(timeout=0)
                                running_node_evaluation.pop(node_id)
                            except Exception as e:
                                log_metadata.error(f"Node eval #{node_id} failed: {e}")

                        # node execution future ---------------------------
                        if inflight_exec.is_done():
                            running_node_execution.pop(node_id)
                            continue

                        if output := inflight_exec.pop_output():
                            node_output_found = True
                            running_node_evaluation[node_id] = (
                                asyncio.run_coroutine_threadsafe(
                                    self._process_node_output(
                                        output=output,
                                        node_id=node_id,
                                        graph_exec=graph_exec,
                                        log_metadata=log_metadata,
                                        nodes_input_masks=nodes_input_masks,
                                        execution_queue=execution_queue,
                                    ),
                                    self.node_evaluation_loop,
                                )
                            )
                    if (
                        not node_output_found
                        and execution_queue.empty()
                        and (running_node_execution or running_node_evaluation)
                    ):
                        cluster_lock.refresh()
                        time.sleep(0.1)

            # loop done --------------------------------------------------

            # Output moderation
            try:
                if moderation_error := asyncio.run_coroutine_threadsafe(
                    automod_manager.moderate_graph_execution_outputs(
                        db_client=get_db_async_client(),
                        graph_exec_id=graph_exec.graph_exec_id,
                        user_id=graph_exec.user_id,
                        graph_id=graph_exec.graph_id,
                    ),
                    self.node_evaluation_loop,
                ).result(timeout=30.0):
                    raise moderation_error
            except asyncio.TimeoutError:
                log_metadata.warning(
                    f"Output moderation timed out for graph execution {graph_exec.graph_exec_id}, bypassing moderation and continuing execution"
                )
                # Continue execution without moderation

            # Determine final execution status based on whether there was an error or termination
            if cancel.is_set():
                execution_status = ExecutionStatus.TERMINATED
            elif error is not None:
                execution_status = ExecutionStatus.FAILED
            else:
                if db_client.has_pending_reviews_for_graph_exec(
                    graph_exec.graph_exec_id
                ):
                    execution_status = ExecutionStatus.REVIEW
                else:
                    execution_status = ExecutionStatus.COMPLETED

            if error:
                execution_stats.error = str(error) or type(error).__name__

            return execution_status

        except BaseException as e:
            error = (
                e
                if isinstance(e, Exception)
                else Exception(f"{e.__class__.__name__}: {e}")
            )
            if not execution_stats.error:
                execution_stats.error = str(error)

            known_errors = (InsufficientBalanceError, ModerationError)
            if isinstance(error, known_errors):
                return ExecutionStatus.FAILED

            execution_status = ExecutionStatus.FAILED
            log_metadata.exception(
                f"Failed graph execution {graph_exec.graph_exec_id}: {error}"
            )

            # Send rate-limited Discord alert for unknown/unexpected errors
            send_rate_limited_discord_alert(
                "graph_execution",
                error,
                "unknown_error",
                f"🚨 **Unknown Graph Execution Error**\n"
                f"User: {graph_exec.user_id}\n"
                f"Graph ID: {graph_exec.graph_id}\n"
                f"Execution ID: {graph_exec.graph_exec_id}\n"
                f"Error Type: {type(error).__name__}\n"
                f"Error: {str(error)[:200]}{'...' if len(str(error)) > 200 else ''}\n",
            )

            raise

        finally:
            self._cleanup_graph_execution(
                execution_queue=execution_queue,
                running_node_execution=running_node_execution,
                running_node_evaluation=running_node_evaluation,
                execution_status=execution_status,
                error=error,
                graph_exec_id=graph_exec.graph_exec_id,
                log_metadata=log_metadata,
                db_client=db_client,
            )