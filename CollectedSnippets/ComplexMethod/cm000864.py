def _handle_run_message(
        self,
        _channel: BlockingChannel,
        method: Basic.Deliver,
        _properties: BasicProperties,
        body: bytes,
    ):
        """Handle run message from DIRECT exchange."""
        delivery_tag = method.delivery_tag
        # Capture the channel used at message delivery time to ensure we ack
        # on the correct channel. Delivery tags are channel-scoped and become
        # invalid if the channel is recreated after reconnection.
        delivery_channel = _channel

        def ack_message(reject: bool, requeue: bool):
            """Acknowledge or reject the message.

            Uses the channel from the original message delivery. If the channel
            is no longer open (e.g., after reconnection), logs a warning and
            skips the ack - RabbitMQ will redeliver the message automatically.
            """
            try:
                if not delivery_channel.is_open:
                    logger.warning(
                        f"Channel closed, cannot ack delivery_tag={delivery_tag}. "
                        "Message will be redelivered by RabbitMQ."
                    )
                    return

                if reject:
                    delivery_channel.connection.add_callback_threadsafe(
                        lambda: delivery_channel.basic_nack(
                            delivery_tag, requeue=requeue
                        )
                    )
                else:
                    delivery_channel.connection.add_callback_threadsafe(
                        lambda: delivery_channel.basic_ack(delivery_tag)
                    )
            except (AMQPChannelError, AMQPConnectionError) as e:
                # Channel/connection errors indicate stale delivery tag - don't retry
                logger.warning(
                    f"Cannot ack delivery_tag={delivery_tag} due to channel/connection "
                    f"error: {e}. Message will be redelivered by RabbitMQ."
                )
            except Exception as e:
                # Other errors might be transient, but log and skip to avoid blocking
                logger.error(
                    f"Unexpected error acking delivery_tag={delivery_tag}: {e}"
                )

        # Check if we're shutting down
        if self.stop_consuming.is_set():
            logger.info("Rejecting new task during shutdown")
            ack_message(reject=True, requeue=True)
            return

        # Check if we can accept more tasks
        self._cleanup_completed_tasks()
        if len(self.active_tasks) >= self.pool_size:
            ack_message(reject=True, requeue=True)
            return

        try:
            entry = CoPilotExecutionEntry.model_validate_json(body)
        except Exception as e:
            logger.error(f"Could not parse run message: {e}, body={body}")
            ack_message(reject=True, requeue=False)
            return

        session_id = entry.session_id

        # Check for local duplicate - session is already running on this executor
        if session_id in self.active_tasks:
            logger.warning(
                f"Session {session_id} already running locally, rejecting duplicate"
            )
            ack_message(reject=True, requeue=False)
            return

        # Try to acquire cluster-wide lock
        cluster_lock = ClusterLock(
            redis=redis.get_redis(),
            key=get_session_lock_key(session_id),
            owner_id=self.executor_id,
            timeout=settings.config.cluster_lock_timeout,
        )
        current_owner = cluster_lock.try_acquire()
        if current_owner != self.executor_id:
            if current_owner is not None:
                logger.warning(
                    f"Session {session_id} already running on pod {current_owner}"
                )
                ack_message(reject=True, requeue=False)
            else:
                logger.warning(
                    f"Could not acquire lock for {session_id} - Redis unavailable"
                )
                ack_message(reject=True, requeue=True)
            return

        # Execute the task
        try:
            logger.info(
                f"Acquired cluster lock for {session_id}, "
                f"executor_id={self.executor_id}"
            )

            self._task_locks[session_id] = cluster_lock
            cancel_event = threading.Event()
            future = self.executor.submit(
                execute_copilot_turn, entry, cancel_event, cluster_lock
            )
            self.active_tasks[session_id] = (future, cancel_event)
        except Exception as e:
            logger.warning(f"Failed to setup execution for {session_id}: {e}")
            cluster_lock.release()
            if session_id in self._task_locks:
                del self._task_locks[session_id]
            ack_message(reject=True, requeue=True)
            return

        self._update_metrics()

        def on_run_done(f: Future):
            logger.info(f"Run completed for {session_id}")
            error_msg = None
            try:
                if exec_error := f.exception():
                    error_msg = str(exec_error) or type(exec_error).__name__
                    logger.error(f"Execution for {session_id} failed: {error_msg}")
                    ack_message(reject=True, requeue=False)
                else:
                    ack_message(reject=False, requeue=False)
            except asyncio.CancelledError:
                logger.info(f"Run completion callback cancelled for {session_id}")
            except BaseException as e:
                error_msg = str(e) or type(e).__name__
                logger.exception(f"Error in run completion callback: {error_msg}")
            finally:
                if session_id in self._task_locks:
                    logger.info(f"Releasing cluster lock for {session_id}")
                    self._task_locks[session_id].release()
                    del self._task_locks[session_id]
                self._cleanup_completed_tasks()

        future.add_done_callback(on_run_done)