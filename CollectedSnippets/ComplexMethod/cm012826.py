def benchmark_gpu(
        self: Self,
        _callable: Callable[[], Any],
        is_vetted_benchmarking: bool = False,
        **kwargs: Any,
    ) -> float:
        """Benchmark the GPU callable, `_callable`, and return the runtime, in milliseconds.

        Arguments:
        - _callable: The GPU callable to benchmark.

        Keyword Arguments:
        - quantiles: Optionally, a tuple of floats denoting the requested quantiles.
        - return_mode: Optionally, the requested return mode. Currently, Triton's
        `do_bench` supports min, max, mean, and median return modes.
        - **kwargs: Additional kwargs passed to Triton's `do_bench`.

        Returns:
        - The runtime of `callable`, in milliseconds. If `kwargs["quantiles"]` is specified,
        this is the first requested quantile. Else, if `kwargs["return_mode"]` is specified,
        this is the requested return mode. Otherwise, this is the median.
        """
        if not is_vetted_benchmarking:
            may_ban_benchmarking()

        do_bench_params = inspect.signature(self.triton_do_bench).parameters
        for kwarg in list(kwargs.keys()):
            if kwarg not in do_bench_params:
                del kwargs[kwarg]
        try:
            if "quantiles" in kwargs:
                return self.triton_do_bench(_callable, **kwargs)[0]
            elif "return_mode" in kwargs:
                return self.triton_do_bench(_callable, **kwargs)
            return self.triton_do_bench(_callable, **kwargs, return_mode="median")
        except Exception as e:
            # ErrorInvalidConfiguration
            # Return inf to skip this config during autotuning
            error_str = str(e).lower()
            if "invalid configuration" in error_str:
                logger.warning(
                    "Skipping benchmark due to invalid configuration error: %s",
                    error_str,
                )
                return float("inf")
            raise