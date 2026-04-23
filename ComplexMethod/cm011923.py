def do_autotuning(
        self,
        name,
        input_nodes,
        layout,
        input_gen_fns,
        inputs_key,
        choices,
        precompile_fn,
        hint_override: int | None = None,
        best_config_future=None,
        is_collective=False,
    ):
        """Execute the autotuning process for kernel algorithm selection.

        This method orchestrates the complete autotuning pipeline including precompilation,
        prescreening, benchmarking, and feedback collection to select the optimal kernel
        implementation for given inputs.

        Args:
            name: Name identifier for the operation being autotuned (e.g., 'mm', 'convolution').
            input_nodes: List of input IR nodes used for benchmarking.
            layout: Layout information specifying device and memory format for the operation.
            input_gen_fns: Optional dict mapping argument indices to functions that generate
                torch.Tensor inputs from ir.Buffer for benchmarking. If provided, these are
                used instead of random tensors.
            inputs_key: Cache key representing the input characteristics (sizes, strides, dtypes).
            choices: List of ChoiceCaller objects representing candidate kernel implementations.
            precompile_fn: Callable that precompiles all kernel choices before benchmarking.
            hint_override: Optional index to override which choice is selected, used for testing
                or forced selection.
            best_config_future: Optional future containing pre-determined best configuration to
                filter choices by specific config parameters.

        Returns:
            dict: Mapping from ChoiceCaller to benchmark timing in seconds. Choices with
                non-finite timings (inf/nan) indicate failures.

        Raises:
            NoValidChoicesError: When all choices fail to compile or benchmark, or when all
                timing results are non-finite.
        """
        if log.isEnabledFor(logging.DEBUG) and not use_pipelined_autotuning():
            # Log shape information for debugging timeout issues
            sizevars = V.graph.sizevars

            shapes = [
                "x".join(
                    map(
                        str,
                        sizevars.optimization_hints_with_override(
                            node.get_size(),
                            hint_override=hint_override,
                        ),
                    )
                )
                for node in input_nodes
            ]
            log.debug(
                "[BENCHMARK DEBUG] Starting autotuning for '%s' with shapes: %s, device: %s",
                name,
                shapes,
                layout.device.type if layout else "unknown",
            )

        precompile_start_ts = time.time()

        if not use_pipelined_autotuning():
            with dynamo_timed(
                f"{name}_template_precompiling",
                log_pt2_compile_event=True,
                dynamo_compile_column_us="compile_time_autotune_time_us",
            ):
                precompile_times = precompile_fn()
        else:
            precompile_times = precompile_fn()

        precompile_elapse = time.time() - precompile_start_ts
        log.debug("Precompilation elapsed time: %.02fs", precompile_elapse)
        # Prune anything that failed to compile
        choices = [c for c in choices if not c.failed]
        if len(choices) == 0:
            raise self.create_no_valid_choices(
                name, "All choices failed to compile for backend."
            )

        candidates = self.prescreen_choices(
            choices, name, inputs_key, self.prescreening_cache
        )
        prescreening_elapse: float | None = None
        if candidates:
            prescreening_start_ts = time.time()
            timings = self.lookup(
                candidates,
                name,
                inputs_key,
                lambda choices: self.autotune(
                    name,
                    input_nodes,
                    layout,
                    input_gen_fns,
                    choices,
                    hint_override=hint_override,
                ),
                hint_override=hint_override,
            )
            choices = self.prune_choices_postscreen(
                choices, timings, name, inputs_key, self.prescreening_cache
            )
            prescreening_elapse = time.time() - prescreening_start_ts
            log.debug("Prescreening elapsed time: %.02fs", prescreening_elapse)

        if use_pipelined_autotuning():
            AsyncAutotuner.start(choices, inputs_key)
            return

        autotune_start_ts = time.time()

        if best_config_future is not None:
            best_config = await_sync(best_config_future)

            important_keys = [
                "ACC_TYPE",
                "ALLOW_TF32",
                "BLOCK_K",
                "BLOCK_M",
                "BLOCK_N",
                "EVEN_K",
                "GROUP_M",
                "USE_FAST_ACCUM",
                "num_stages",
                "num_warps",
                "num_consumer_groups",
                "num_buffers_warp_spec",
            ]
            choices = [
                choice
                for choice in choices
                if all(
                    f"{k}={best_config[k]}" in choice.description
                    for k in important_keys
                )
                for k in important_keys
            ]
            log.info("Filtered to %d choices based on best_config", len(choices))

        has_autotuned: bool = False

        def track_has_autotuned(choices):
            nonlocal has_autotuned
            has_autotuned = True
            return self.autotune(
                name,
                input_nodes,
                layout,
                input_gen_fns,
                choices,
                hint_override=hint_override,
                is_collective=is_collective,
            )

        timings = self.lookup(
            choices,
            name,
            inputs_key,
            track_has_autotuned,
            hint_override=hint_override,
        )

        autotune_elapse = time.time() - autotune_start_ts
        log.debug("Autotuning elapsed time: %.02fs", autotune_elapse)

        # For collective: if any choice returned inf (timeout or failure), fallback to default
        if is_collective and timings:
            has_inf = any(not math.isfinite(timing) for timing in timings.values())
            if has_inf:
                log.warning(
                    "At least one choice failed or timed out during collective benchmarking. "
                    "Falling back to default implementation."
                )
                return {}

        # For regular: if all choices returned inf, raise error
        if timings and all(not math.isfinite(timing) for timing in timings.values()):
            raise NoValidChoicesError

        if (
            has_autotuned
            or log.getEffectiveLevel() == logging.DEBUG
            or config.trace.log_autotuning_results
        ):
            self.log_results(
                name,
                input_nodes,
                timings,
                autotune_elapse,
                precompile_elapse,
                prescreening_elapse,
                hint_override=hint_override,
                is_collective=is_collective,
            )

        def profiler_bench_function(choices_override=None):
            # we're not running through the normal caching autotuner method here because we want to avoid returning
            # the cached value.
            # Avoid benchmarking in a separate process because it's not easy to signal to the TuningProcess that we
            # should use the profiler.
            # If choices_override is provided, only benchmark those choices instead of all choices.
            choices_to_benchmark = (
                choices_override if choices_override is not None else choices
            )
            with config.patch(
                profile_bandwidth_with_do_bench_using_profiling=True,
                autotune_in_subproc=False,
            ):
                return self.benchmark(
                    choices_to_benchmark, input_nodes, layout, input_gen_fns
                )

        for feedback_fn in self.feedback_saver_fns:
            # re-benchmarking the same choices with profiler is a bit expensive, so pass it in as a thunk.
            feedback_fn(
                timings,
                name,
                input_nodes,
                choices,
                profiler_bench_function,
                precompile_times,
            )

        return timings