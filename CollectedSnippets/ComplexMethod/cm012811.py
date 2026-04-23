def run(
        self,
        *args,
        stream,
        benchmark_run=False,
        **kwargs,
    ):  # type:ignore[override]
        """Launch triton kernel call and return result."""
        debug_mode = get_active_debug_mode()
        if debug_mode:
            arg_names = list(self.triton_meta.get("signature", {}).keys())
            kernel_kwargs = dict(zip(arg_names, args))
            kernel_kwargs.update(kwargs)
            self._debug_call = debug_mode.record_triton_kernel(
                kernel_name=self.fn.__name__, kwargs=kernel_kwargs
            )

        if hasattr(triton, "set_allocator"):

            def alloc_fn(size: int, align: int, stream: int | None):
                return torch.empty(
                    size, dtype=torch.int8, device=self.device_props.type
                )

            triton.set_allocator(alloc_fn)

        if self.triton_interpret:
            args, grid = self._interpret_args_grid(args, self.configs[0])
            return self.fn[grid](
                *args,
                **kwargs,
                **self.configs[0].kwargs,
            )

        if len(self.launchers) != 1:
            if len(self.launchers) == 0:
                start_time = time.time_ns()
                self.precompile()
                self.precompile_time_taken_ns = time.time_ns() - start_time
            if len(self.launchers) > 1:
                self.autotune_to_one_config(*args, **kwargs)

        if self.inductor_meta.get("combo_tuning_groups") and not getattr(
            self.launchers[0].config, "found_by_combo_autotune", False
        ):
            with dynamo_timed(
                "CachingAutotuner.combo_sequential_autotune",
                log_pt2_compile_event=False,
                metadata={"kernel_name": self.inductor_meta.get("kernel_name")},
                dynamo_compile_column_us="runtime_triton_autotune_time_us",
                compile_id=self.compile_id,
                is_backward=self.is_backward,
                log_waitcounter=True,
                waitcounter_name_override="triton_autotuner",
            ):
                self.launchers = [
                    self._combo_sequential_autotune(self.launchers[0], *args, **kwargs)
                ]

        if not getattr(
            self.launchers[0].config, "found_by_coordesc", False
        ) and self.inductor_meta.get("coordinate_descent_tuning", False):
            self.launchers = [
                self.coordinate_descent_tuning(self.launchers[0], *args, **kwargs)
            ]

        (launcher,) = self.launchers
        # Ensure the final launcher is marked as a winner for bundle filtering.
        # For multi-config autotuning and coordesc, put_winner was already called
        # (this is an idempotent set-add). For single-config kernels that skip
        # autotuning entirely, this is the only call site that records the winner.
        TritonBundler.put_winner(launcher.cache_hash)
        if launcher.store_cubin and (not benchmark_run or not self.cuda_kernel_saved):
            self.save_gpu_kernel(stream, launcher)

        try:
            self._pre_launch(launcher, *args, stream=stream, **kwargs)
            result = launcher(*args, **kwargs, stream=stream)
        finally:
            self._post_launch()
        return result