def _handle_run_message(
        self,
        _channel: BlockingChannel,
        method: Basic.Deliver,
        _properties: BasicProperties,
        body: bytes,
    ):
        delivery_tag = method.delivery_tag

        @func_retry
        def _ack_message(reject: bool, requeue: bool):
            """
            Acknowledge or reject the message based on execution status.

            Args:
                reject: Whether to reject the message
                requeue: Whether to requeue the message
            """

            # Connection can be lost, so always get a fresh channel
            channel = self.run_client.get_channel()
            if reject:
                if requeue and settings.config.requeue_by_republishing:
                    # Send rejected message to back of queue using republishing
                    def _republish_to_back():
                        try:
                            # First republish to back of queue
                            self.run_client.publish_message(
                                routing_key=GRAPH_EXECUTION_ROUTING_KEY,
                                message=body.decode(),  # publish_message expects string, not bytes
                                exchange=GRAPH_EXECUTION_EXCHANGE,
                            )
                            # Then reject without requeue (message already republished)
                            channel.basic_nack(delivery_tag, requeue=False)
                            logger.info("Message requeued to back of queue")
                        except Exception as e:
                            logger.error(
                                f"[{self.service_name}] Failed to requeue message to back: {e}"
                            )
                            # Fall back to traditional requeue on failure
                            channel.basic_nack(delivery_tag, requeue=True)

                    channel.connection.add_callback_threadsafe(_republish_to_back)
                else:
                    # Traditional requeue (goes to front) or no requeue
                    channel.connection.add_callback_threadsafe(
                        lambda: channel.basic_nack(delivery_tag, requeue=requeue)
                    )
            else:
                channel.connection.add_callback_threadsafe(
                    lambda: channel.basic_ack(delivery_tag)
                )

        # Check if we're shutting down - reject new messages but keep connection alive
        if self.stop_consuming.is_set():
            logger.info(
                f"[{self.service_name}] Rejecting new execution during shutdown"
            )
            _ack_message(reject=True, requeue=True)
            return

        # Check if we can accept more runs
        self._cleanup_completed_runs()
        if len(self.active_graph_runs) >= self.pool_size:
            _ack_message(reject=True, requeue=True)
            return

        try:
            graph_exec_entry = GraphExecutionEntry.model_validate_json(body)
        except Exception as e:
            logger.error(
                f"[{self.service_name}] Could not parse run message: {e}, body={body}"
            )
            _ack_message(reject=True, requeue=False)
            return

        graph_exec_id = graph_exec_entry.graph_exec_id
        user_id = graph_exec_entry.user_id
        graph_id = graph_exec_entry.graph_id
        root_exec_id = graph_exec_entry.execution_context.root_execution_id
        parent_exec_id = graph_exec_entry.execution_context.parent_execution_id

        logger.info(
            f"[{self.service_name}] Received RUN for graph_exec_id={graph_exec_id}, user_id={user_id}, executor_id={self.executor_id}"
            + (f", root={root_exec_id}" if root_exec_id else "")
            + (f", parent={parent_exec_id}" if parent_exec_id else "")
        )

        # Check if root execution is already terminated (prevents orphaned child executions)
        if root_exec_id and root_exec_id != graph_exec_id:
            parent_exec = get_db_client().get_graph_execution_meta(
                execution_id=root_exec_id,
                user_id=user_id,
            )
            if parent_exec and parent_exec.status == ExecutionStatus.TERMINATED:
                logger.info(
                    f"[{self.service_name}] Skipping execution {graph_exec_id} - parent {root_exec_id} is TERMINATED"
                )
                # Mark this child as terminated since parent was stopped
                get_db_client().update_graph_execution_stats(
                    graph_exec_id=graph_exec_id,
                    status=ExecutionStatus.TERMINATED,
                )
                _ack_message(reject=False, requeue=False)
                return

        # Check user rate limit before processing
        try:
            # Only check executions from the last 24 hours for performance
            current_running_count = get_db_client().get_graph_executions_count(
                user_id=user_id,
                graph_id=graph_id,
                statuses=[ExecutionStatus.RUNNING],
                created_time_gte=datetime.now(timezone.utc) - timedelta(hours=24),
            )

            if (
                current_running_count
                >= settings.config.max_concurrent_graph_executions_per_user
            ):
                logger.warning(
                    f"[{self.service_name}] Rate limit exceeded for user {user_id} on graph {graph_id}: "
                    f"{current_running_count}/{settings.config.max_concurrent_graph_executions_per_user} running executions"
                )
                _ack_message(reject=True, requeue=True)
                return

        except Exception as e:
            logger.error(
                f"[{self.service_name}] Failed to check rate limit for user {user_id}: {e}, proceeding with execution"
            )
            # If rate limit check fails, proceed to avoid blocking executions

        # Check for local duplicate execution first
        if graph_exec_id in self.active_graph_runs:
            logger.warning(
                f"[{self.service_name}] Graph {graph_exec_id} already running locally; rejecting duplicate."
            )
            _ack_message(reject=True, requeue=True)
            return

        # Try to acquire cluster-wide execution lock
        cluster_lock = ClusterLock(
            redis=redis.get_redis(),
            key=f"exec_lock:{graph_exec_id}",
            owner_id=self.executor_id,
            timeout=settings.config.cluster_lock_timeout,
        )
        current_owner = cluster_lock.try_acquire()
        if current_owner != self.executor_id:
            # Either someone else has it or Redis is unavailable
            if current_owner is not None:
                logger.warning(
                    f"[{self.service_name}] Graph {graph_exec_id} already running on pod {current_owner}, current executor_id={self.executor_id}"
                )
                _ack_message(reject=True, requeue=False)
            else:
                logger.warning(
                    f"[{self.service_name}] Could not acquire lock for {graph_exec_id} - Redis unavailable"
                )
                _ack_message(reject=True, requeue=True)
            return

        # Wrap entire block after successful lock acquisition
        try:
            self._execution_locks[graph_exec_id] = cluster_lock

            logger.info(
                f"[{self.service_name}] Successfully acquired cluster lock for {graph_exec_id}, executor_id={self.executor_id}"
            )

            cancel_event = threading.Event()
            future = self.executor.submit(
                execute_graph, graph_exec_entry, cancel_event, cluster_lock
            )
            self.active_graph_runs[graph_exec_id] = (future, cancel_event)
        except Exception as e:
            logger.warning(
                f"[{self.service_name}] Failed to setup execution for {graph_exec_id}: {type(e).__name__}: {e}"
            )
            # Release cluster lock before requeue
            cluster_lock.release()
            if graph_exec_id in self._execution_locks:
                del self._execution_locks[graph_exec_id]
            _ack_message(reject=True, requeue=True)
            return
        self._update_prompt_metrics()

        def _on_run_done(f: Future):
            logger.info(f"[{self.service_name}] Run completed for {graph_exec_id}")
            try:
                if exec_error := f.exception():
                    logger.error(
                        f"[{self.service_name}] Execution for {graph_exec_id} failed: {type(exec_error)} {exec_error}"
                    )
                    _ack_message(reject=True, requeue=True)
                else:
                    _ack_message(reject=False, requeue=False)
            except BaseException as e:
                logger.exception(
                    f"[{self.service_name}] Error in run completion callback: {e}"
                )
            finally:
                # Release the cluster-wide execution lock
                if graph_exec_id in self._execution_locks:
                    logger.info(
                        f"[{self.service_name}] Releasing cluster lock for {graph_exec_id}, executor_id={self.executor_id}"
                    )
                    self._execution_locks[graph_exec_id].release()
                    del self._execution_locks[graph_exec_id]
                self._cleanup_completed_runs()

        future.add_done_callback(_on_run_done)