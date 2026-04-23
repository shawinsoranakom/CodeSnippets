def cleanup(self):
        """Override cleanup to implement graceful shutdown with active execution waiting."""
        prefix = f"[{self.service_name}][on_graph_executor_stop {os.getpid()}]"
        logger.info(f"{prefix} 🧹 Starting graceful shutdown...")

        # Signal the consumer thread to stop (thread-safe)
        try:
            self.stop_consuming.set()
            run_channel = self.run_client.get_channel()
            run_channel.connection.add_callback_threadsafe(
                lambda: run_channel.stop_consuming()
            )
            logger.info(f"{prefix} ✅ Exec consumer has been signaled to stop")
        except Exception as e:
            logger.warning(
                f"{prefix} ⚠️ Error signaling consumer to stop: {type(e)} {e}"
            )

        # Wait for active executions to complete
        if self.active_graph_runs:
            logger.info(
                f"{prefix} ⏳ Waiting for {len(self.active_graph_runs)} active executions to complete..."
            )

            max_wait = GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS
            wait_interval = 5
            waited = 0

            while waited < max_wait:
                self._cleanup_completed_runs()
                if not self.active_graph_runs:
                    logger.info(f"{prefix} ✅ All active executions completed")
                    break
                else:
                    ids = [k.split("-")[0] for k in self.active_graph_runs.keys()]
                    logger.info(
                        f"{prefix} ⏳ Still waiting for {len(self.active_graph_runs)} executions: {ids}"
                    )

                    for graph_exec_id in self.active_graph_runs:
                        if lock := self._execution_locks.get(graph_exec_id):
                            lock.refresh()

                time.sleep(wait_interval)
                waited += wait_interval

            if self.active_graph_runs:
                logger.warning(
                    f"{prefix} ⚠️ {len(self.active_graph_runs)} executions still running after {max_wait}s"
                )
            else:
                logger.info(f"{prefix} ✅ All executions completed gracefully")

        # Shutdown the executor
        try:
            self.executor.shutdown(cancel_futures=True, wait=False)
            logger.info(f"{prefix} ✅ Executor shutdown completed")
        except Exception as e:
            logger.warning(f"{prefix} ⚠️ Error during executor shutdown: {type(e)} {e}")

        # Release remaining execution locks
        try:
            for lock in self._execution_locks.values():
                lock.release()
            self._execution_locks.clear()
            logger.info(f"{prefix} ✅ Released execution locks")
        except Exception as e:
            logger.warning(f"{prefix} ⚠️ Failed to release all locks: {e}")

        # Disconnect the run execution consumer
        self._stop_message_consumers(
            self.run_thread,
            self.run_client,
            prefix + " [run-consumer]",
        )
        self._stop_message_consumers(
            self.cancel_thread,
            self.cancel_client,
            prefix + " [cancel-consumer]",
        )

        # Drain any in-flight cost log tasks before exit so we don't silently
        # drop INSERT operations during deployments.
        loop = getattr(self, "node_execution_loop", None)
        if loop is not None and loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    drain_pending_cost_logs(), loop
                ).result(timeout=10)
                logger.info(f"{prefix} ✅ Cost log tasks drained")
            except Exception as e:
                logger.warning(f"{prefix} ⚠️ Failed to drain cost log tasks: {e}")

        logger.info(f"{prefix} ✅ Finished GraphExec cleanup")

        super().cleanup()