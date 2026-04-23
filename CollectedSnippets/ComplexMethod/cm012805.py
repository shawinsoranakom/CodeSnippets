def bench(self, launcher, *args, with_profiler=False, **kwargs):
        """Measure the performance of a given launcher."""
        # we don't skip configs with spilled registers when auto-tuning custom
        # (user-written) Triton kernels, as (i) we don't have any knowledge or
        # control over the kernel code; (ii) there is empirical evidence that
        # for some (complicated) custom Triton kernels, a register-spilling
        # config may yield the best latency.
        if (
            not self.custom_kernel
            and launcher.n_spills is not None
            and launcher.n_spills
            > self.inductor_meta.get("spill_threshold", 32 if torch.version.hip else 16)
        ):
            log.debug(
                "Skip config %s because of register spilling: %d",
                launcher.config,
                launcher.n_spills,
            )
            self.benchmark_failure_reasons[launcher] = (
                BenchmarkFailureReason.REGISTER_SPILLING
            )
            return float("inf")

        device_interface = self.get_device_interface()
        stream = device_interface.get_raw_stream(device_interface.current_device())

        cpu_copies = self.copy_args_to_cpu_if_needed(*args, **kwargs)

        def kernel_call():
            cloned_args, cloned_kwargs = self.maybe_clone_args(
                cpu_copies, *args, **kwargs
            )
            # reset to zero before evaluating any config
            self.reset_to_zero_args(*args, **kwargs)
            kernel_name = self.inductor_meta.get("kernel_name", "triton kernel")
            if autograd_profiler._is_profiler_enabled:
                profiler_kwargs = self.get_profiler_kwargs(stream, launcher)
                with torch._C._profiler._RecordFunctionFast(
                    kernel_name,
                    cloned_args,
                    profiler_kwargs,
                ):
                    try:
                        launcher(
                            *cloned_args,
                            **cloned_kwargs,
                            stream=stream,
                        )
                    except Exception:
                        log.error(
                            "Failed during launch %s with config: %s (num_warps=%s, num_stages=%s, kwargs=%s)",
                            kernel_name,
                            launcher.config,
                            launcher.config.num_warps,
                            launcher.config.num_stages,
                            launcher.config.kwargs,
                        )
                        raise

            else:
                try:
                    launcher(
                        *cloned_args,
                        **cloned_kwargs,
                        stream=stream,
                    )
                except Exception:
                    log.error(
                        "Failed during launch %s with config: %s (num_warps=%s, num_stages=%s, kwargs=%s)",
                        kernel_name,
                        launcher.config,
                        launcher.config.num_warps,
                        launcher.config.num_stages,
                        launcher.config.kwargs,
                    )
                    raise
            self.restore_args_from_cpu(cpu_copies)

        # only use profiler when not already in a profiler instance
        if with_profiler and not autograd_profiler._is_profiler_enabled:
            from torch._inductor.utils import do_bench_using_profiling

            return do_bench_using_profiling(kernel_call, warmup=10, rep=40)

        benchmark_kwargs = (
            {}
            if self.device_props.type == "cpu"
            else {"rep": 40, "is_vetted_benchmarking": True}
        )
        result = benchmarker.benchmark(
            fn=kernel_call,
            device=self.device_props.type,
            **benchmark_kwargs,  # type: ignore[arg-type]
        )
        # benchmarker.benchmark() only returns float("inf") when catching an
        # "invalid configuration" exception - all other exceptions are re-raised.
        # Therefore, if result is inf here, it must be due to invalid config.
        if result == float("inf"):
            self.benchmark_failure_reasons[launcher] = (
                BenchmarkFailureReason.INVALID_CONFIG
            )
        return result