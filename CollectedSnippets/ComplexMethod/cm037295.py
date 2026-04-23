def record(
        self,
        scheduler_stats: SchedulerStats | None,
        iteration_stats: IterationStats | None,
        mm_cache_stats: MultiModalCacheStats | None = None,
        engine_idx: int = 0,
    ):
        """Log Stats to standard output."""
        if iteration_stats:
            self._track_iteration_stats(iteration_stats)

        if scheduler_stats is not None:
            self.prefix_caching_metrics.observe(scheduler_stats.prefix_cache_stats)

            if scheduler_stats.connector_prefix_cache_stats is not None:
                self.connector_prefix_caching_metrics.observe(
                    scheduler_stats.connector_prefix_cache_stats
                )

            if scheduler_stats.spec_decoding_stats is not None:
                self.spec_decoding_logging.observe(scheduler_stats.spec_decoding_stats)
            if kv_connector_stats := scheduler_stats.kv_connector_stats:
                self.kv_connector_logging.observe(kv_connector_stats)
            if (
                self.cudagraph_logging is not None
                and scheduler_stats.cudagraph_stats is not None
            ):
                self.cudagraph_logging.observe(scheduler_stats.cudagraph_stats)
            if not self.aggregated:
                self.last_scheduler_stats = scheduler_stats
            if (perf_stats := scheduler_stats.perf_stats) and self._enable_perf_stats():
                self.perf_metrics_logging.observe(perf_stats)
        if mm_cache_stats:
            self.mm_caching_metrics.observe(mm_cache_stats)