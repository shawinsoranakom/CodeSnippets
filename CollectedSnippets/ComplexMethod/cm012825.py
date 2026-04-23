def benchmark(
        self: Self,
        fn: Callable[..., Any],
        fn_args: tuple[Any, ...] | None = None,
        fn_kwargs: dict[str, Any] | None = None,
        device: str | torch.device | None = None,
        **kwargs: Any,
    ) -> float:
        """Benchmark `fn(*fn_args, *fn_kwargs)` and return the runtime, in milliseconds (the
        actual runtime calculation is dictated by the benchmarking implementation, but may be
        one of [mean, median, minimum, etc.]). Functions as a convenience wrapper around
        device-specific implementations, like `benchmark_cpu` and `benchmark_gpu`. Raises
        `ValueError(...)` if we can't safely infer the device type of `fn`; for example,
        if multiple device types are found in `fn_args` and `fn_kwargs`, or if no device
        types are found. To bypass device inference, provide the device to the `device`
        parameter.

        WARNING: if `fn` mutates `fn_args` or `fn_kwargs`, benchmarking may fail unexpectedly.
        For example, if `fn` clears a mutable object, subsequent invocations of `fn` during
        benchmarking will fail. In such cases, `fn` should handle cloning its arguments internally.
        If device inference is required, `Benchmarker.infer_device` can be used prior to calling
        this method without any arguments for `fn_args` and `fn_kwargs`.

        Arguments:
        - fn: The function to benchmark.
        - fn_args: The function's arguments.
        - fn_kwargs: The function's kwargs.

        Keyword Arguments:
        - device: Which device to use for benchmarking. If not provided the device will be attempted
        to be inferred from `fn_args` and `fn_kwargs`.
        - **kwargs: The benchmarking implementation's kwargs.

        Returns:
        - The runtime of `fn(*fn_args, **fn_kwargs)`, in milliseconds.
        """
        inferred_device: torch.device | None = None
        if device is not None:
            inferred_device = (
                torch.device(device) if isinstance(device, str) else device
            )
        else:
            if fn_args is None and fn_kwargs is None:
                raise ValueError(
                    "`fn_args` and `fn_kwargs` cannot both be None if `device` is not provided."
                )

            fn_args = fn_args or tuple()
            fn_kwargs = fn_kwargs or {}
            inferred_device = self.infer_device(*fn_args, **fn_kwargs)

        assert isinstance(inferred_device, torch.device)

        fn_args = fn_args or tuple()
        fn_kwargs = fn_kwargs or {}

        # No need to wrap if the callable takes no arguments
        if len(fn_args) == 0 and len(fn_kwargs) == 0:
            # Keep a true zero-arg callable type to satisfy type checkers.
            def _callable() -> Any:
                return fn()
        else:
            _args = fn_args
            _kwargs = fn_kwargs

            def _callable() -> Any:
                return fn(*_args, **_kwargs)

        warmup = kwargs.pop("warmup", inductor_config.inductor_default_autotune_warmup)
        rep = kwargs.pop("rep", inductor_config.inductor_default_autotune_rep)

        # Surfacing all kernels during autotuning is super noisy; filtering these out.
        with DebugMode._benchmarking_inductor():
            # First, try a registered device-specific benchmarker
            benchmark_fn: Callable[..., Any] | None = _BENCHMARK_DISPATCH.get(
                inferred_device.type
            )
            if benchmark_fn is not None:
                return benchmark_fn(self, _callable, warmup=warmup, rep=rep, **kwargs)

            # Backward-compatible default:
            # - CPU  -> CPU benchmark path
            # - else -> GPU benchmark path (legacy behavior retained for non-CPU)
            if inferred_device == torch.device("cpu"):
                return self.benchmark_cpu(_callable, warmup=warmup, rep=rep, **kwargs)
            return self.benchmark_gpu(_callable, warmup=warmup, rep=rep, **kwargs)