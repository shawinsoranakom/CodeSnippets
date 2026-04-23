def autotune_to_one_config(self, *args, **kwargs):
        """Do the actual autotuning"""
        start_time = time.time_ns()
        timings = self.benchmark_all_configs(*args, **kwargs)
        benchmark_time_taken_ns = time.time_ns() - start_time

        # Check if any configs failed (have inf timing) and log which one was selected
        failed_launchers = [
            launcher for launcher, timing in timings.items() if timing == float("inf")
        ]
        if failed_launchers:
            valid_timings = [(k, v) for k, v in timings.items() if v != float("inf")]
            if valid_timings:
                best_launcher, best_time = min(valid_timings, key=lambda x: x[1])

                # Count failures by reason
                spill_count = sum(
                    1
                    for launcher in failed_launchers
                    if self.benchmark_failure_reasons.get(launcher)
                    == BenchmarkFailureReason.REGISTER_SPILLING
                )
                invalid_config_count = sum(
                    1
                    for launcher in failed_launchers
                    if self.benchmark_failure_reasons.get(launcher)
                    == BenchmarkFailureReason.INVALID_CONFIG
                )

                reason_parts = []
                if spill_count > 0:
                    reason_parts.append(f"{spill_count} register spilling")
                if invalid_config_count > 0:
                    reason_parts.append(f"{invalid_config_count} invalid config")
                reason_str = ", ".join(reason_parts) if reason_parts else "unknown"

                log.info(
                    "Skipped %d/%d configs for %s (%s). Selected: %s (%.4f ms)",
                    len(failed_launchers),
                    len(timings),
                    self.fn.__name__,
                    reason_str,
                    best_launcher.config,
                    best_time,
                )

        self.launchers = [builtins.min(timings, key=timings.get)]
        self.autotune_time_taken_ns = (
            self.precompile_time_taken_ns + benchmark_time_taken_ns
        )

        # log the best config
        launcher = self.launchers[0]
        log.debug(
            "Best config for %s: %s: %f, nreg %d, nspill %d, #shared-mem %s",
            self.fn.__name__,
            launcher.config,
            timings[launcher],
            launcher.n_regs,
            launcher.n_spills,
            launcher.shared,
        )

        TritonBundler.put_winner(launcher.cache_hash)

        if self.save_cache_hook:
            self.save_cache_hook(
                launcher.config,
                self.autotune_time_taken_ns,
                found_by_coordesc=self.inductor_meta.get(
                    "coordinate_descent_tuning", False
                ),
                triton_cache_hash=launcher.cache_hash,
            )