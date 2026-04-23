def log(self):
        self._update_stats()
        self.aggregate_scheduler_stats()
        # Avoid log noise on an idle production system
        log_fn = logger.debug if self.engine_is_idle else logger.info
        # Format and print output.
        log_parts = [
            "Avg prompt throughput: %.1f tokens/s",
            "Avg generation throughput: %.1f tokens/s",
            "Running: %d reqs",
            "Waiting: %d reqs",
        ]
        total_waiting = (
            self.last_scheduler_stats.num_waiting_reqs
            + self.last_scheduler_stats.num_skipped_waiting_reqs
        )
        log_args: list[int | float | str] = [
            self.last_prompt_throughput,
            self.last_generation_throughput,
            self.last_scheduler_stats.num_running_reqs,
            total_waiting,
        ]

        if self.last_scheduler_stats.num_skipped_waiting_reqs > 0:
            log_parts.append("Deferred: %d reqs")
            log_args.append(self.last_scheduler_stats.num_skipped_waiting_reqs)

        if self.num_preemptions > 0:
            log_parts.append("Preemptions: %d")
            log_args.append(self.num_preemptions)

        log_parts.extend(
            [
                "GPU KV cache usage: %.1f%%",
                "Prefix cache hit rate: %.1f%%",
            ]
        )
        log_args.extend(
            [
                self.last_scheduler_stats.kv_cache_usage * 100,
                self.prefix_caching_metrics.hit_rate * 100,
            ]
        )

        if envs.VLLM_COMPUTE_NANS_IN_LOGITS:
            log_parts.append("Corrupted: %d reqs")
            log_args.append(self.num_corrupted_reqs)
        if not self.connector_prefix_caching_metrics.empty:
            log_parts.append("External prefix cache hit rate: %.1f%%")
            log_args.append(self.connector_prefix_caching_metrics.hit_rate * 100)
        if not self.mm_caching_metrics.empty:
            log_parts.append("MM cache hit rate: %.1f%%")
            log_args.append(self.mm_caching_metrics.hit_rate * 100)

        log_fn(
            self.log_prefix + ", ".join(log_parts),
            *log_args,
        )

        self.spec_decoding_logging.log(log_fn=log_fn)
        self.kv_connector_logging.log(log_fn=log_fn)
        if self.cudagraph_logging is not None:
            self.cudagraph_logging.log(log_fn=log_fn)
        if self._enable_perf_stats():
            self.perf_metrics_logging.log(log_fn=log_fn, log_prefix=self.log_prefix)