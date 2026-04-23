def cleanup(self):
        """Graceful shutdown — mirrors ``backend.executor.manager`` pattern.

        1. Stop consumer immediately (both the Python flag that gates
           ``_handle_run_message`` and ``channel.stop_consuming()`` at
           the broker), so no new work enters.
        2. Passively wait for ``active_tasks`` to drain — each turn's
           own ``finally`` publishes its terminal state via
           ``mark_session_completed``. When a turn exits, ``on_run_done``
           removes it from ``active_tasks`` and releases its cluster lock.
        3. Shut down the thread-pool executor (cancels pending, leaves
           running threads alone — process exit handles them).
        4. Release any cluster locks still held (defensive — on_run_done's
           finally should have already released them).
        5. Stop message consumer threads + disconnect pika clients.

        The zombie-session bug this PR targets is handled inside each
        turn's own lifecycle by :func:`sync_fail_close_session`, NOT by
        cleanup — so cleanup can stay as a simple "wait, then teardown"
        and matches agent-executor's proven pattern.
        """
        pid = os.getpid()
        prefix = f"[cleanup {pid}]"
        logger.info(f"{prefix} Starting graceful shutdown...")

        # 1. Stop consumer — flag AND broker-side
        try:
            self.stop_consuming.set()
            run_channel = self.run_client.get_channel()
            run_channel.connection.add_callback_threadsafe(
                lambda: run_channel.stop_consuming()
            )
            logger.info(f"{prefix} Consumer has been signaled to stop")
        except Exception as e:
            logger.error(f"{prefix} Error stopping consumer: {e}")

        # 2. Wait for in-flight turns to finish naturally
        if self.active_tasks:
            logger.info(
                f"{prefix} Waiting for {len(self.active_tasks)} active tasks "
                f"to complete (timeout: {GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS}s)..."
            )

            start_time = time.monotonic()
            last_refresh = start_time
            lock_refresh_interval = settings.config.cluster_lock_timeout / 10

            while (
                self.active_tasks
                and (time.monotonic() - start_time) < GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS
            ):
                self._cleanup_completed_tasks()
                if not self.active_tasks:
                    break

                now = time.monotonic()
                if now - last_refresh >= lock_refresh_interval:
                    for lock in list(self._task_locks.values()):
                        try:
                            lock.refresh()
                        except Exception as e:
                            logger.warning(f"{prefix} Failed to refresh lock: {e}")
                    last_refresh = now

                logger.info(
                    f"{prefix} {len(self.active_tasks)} tasks still active, waiting..."
                )
                time.sleep(10.0)

            if self.active_tasks:
                logger.warning(
                    f"{prefix} {len(self.active_tasks)} tasks still running after "
                    f"{GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS}s — process exit will "
                    f"abandon them; RabbitMQ redelivery handles the message."
                )

        # 3. Stop message consumer threads
        if self._run_thread:
            self._stop_message_consumers(
                self._run_thread, self.run_client, f"{prefix} [run]"
            )
        if self._cancel_thread:
            self._stop_message_consumers(
                self._cancel_thread, self.cancel_client, f"{prefix} [cancel]"
            )

        # 4. Worker cleanup + executor shutdown
        if self._executor:
            from .processor import cleanup_worker

            logger.info(f"{prefix} Cleaning up workers...")
            futures = []
            for _ in range(self._executor._max_workers):
                futures.append(self._executor.submit(cleanup_worker))
            for f in futures:
                try:
                    f.result(timeout=10)
                except Exception as e:
                    logger.warning(f"{prefix} Worker cleanup error: {e}")

            logger.info(f"{prefix} Shutting down executor...")
            self._executor.shutdown(wait=False)

        # 5. Release any cluster locks still held
        for session_id, lock in list(self._task_locks.items()):
            try:
                lock.release()
                logger.info(f"{prefix} Released lock for {session_id}")
            except Exception as e:
                logger.error(f"{prefix} Failed to release lock for {session_id}: {e}")

        logger.info(f"{prefix} Graceful shutdown completed")