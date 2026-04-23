def stop(self, block: bool = True, timeout: float | None = None, keep_for_next_session: bool = False) -> None:
        """Signal the background thread to stop.

        Args:
            block: Whether to wait for the thread to stop
            timeout: Maximum time to wait for the thread to stop
            keep_for_next_session: Whether to cache this on the model for future use
        """
        if self.batch_processor is None:
            logger.warning("\nBatch processor was not initialized.")
        elif self.batch_processor.cache.use_prefix_sharing:
            logger.info(
                f"\nPrefix sharing was on. Total prefix length: {self.batch_processor.cache._total_prefix_length}"
            )

        if self._generation_thread is None:
            suffix = " Hence the unstarted manager will not be kept for next session." if keep_for_next_session else ""
            logger.warning("Manager not started." + suffix)
            return

        stop_trigger_time = perf_counter()
        if not self.stop_event.is_set():
            self.stop_event.set()
            logger.info("Stopping continuous batching manager...")

        if block:
            self.join(stop_trigger_time, timeout)

        # If the manager is not being kept for next session, we clear the batch processor
        if not keep_for_next_session:
            self.batch_processor = None
        # Otherwise, we keep the batch processor and cache the manager as a model attribute
        else:
            logger.info("Continuous batching manager will be kept for next session.")
            self.model._cached_continuous_batching_manager = self
        # In all cases, a little cleanup is good
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()