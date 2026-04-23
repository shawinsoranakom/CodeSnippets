def __init__(
        self,
        fn,
        triton_meta,  # passed directly to triton
        configs,
        save_cache_hook,
        mutated_arg_names: list[str],  # see [Note: clone mutated buffers]
        optimize_mem,
        heuristic_type,
        size_hints=None,
        inductor_meta=None,  # metadata not relevant to triton
        custom_kernel=False,  # whether the kernel is inductor-generated or custom
        filename: str | None = None,
        reset_to_zero_arg_names: list[str] | None = None,
        autotune_cache_info: dict[str, Any] | None = None,
    ):
        super().__init__()

        assert len(configs) > 0, "Non-empty TritonConfig list required for compiling"
        # makes sure there are no pre-hooks on any of the triton configs
        for cfg in configs:
            validate_triton_config(cfg)

        self.fn = fn
        self.device_props: DeviceProperties = triton_meta["device"]
        self.triton_meta = {
            **triton_meta,
            "device": self.device_props.index,
            "device_type": self.device_props.type,
        }
        self.inductor_meta = {} if inductor_meta is None else inductor_meta
        # Add device properties to inductor_meta for use by coordinate descent tuner
        self.inductor_meta["warp_size"] = self.device_props.warp_size
        self.inductor_meta["max_threads_per_block"] = (
            self.device_props.max_threads_per_block
        )
        self.deterministic_mode = self.inductor_meta.get("deterministic", False)

        self.save_cache_hook = save_cache_hook
        self.mutated_arg_names = mutated_arg_names
        self.reset_to_zero_arg_names = (
            [] if reset_to_zero_arg_names is None else reset_to_zero_arg_names
        )
        self.optimize_mem = optimize_mem
        cached_config = lookup_autotune_config(size_hints, fn)
        self.configs = [cached_config] if cached_config else configs

        self.heuristic_type = heuristic_type
        self.custom_kernel = custom_kernel
        self.cuda_kernel_saved = False
        self.autotune_cache_info = autotune_cache_info
        if log.isEnabledFor(logging.DEBUG):
            log.debug(
                "CachingAutotuner gets %d configs for %s",
                len(self.configs),
                self.fn.__name__,
            )
            for c in self.configs:
                log.debug(c)

        self.compile_results: list[CompileResult[_KernelType]] = []
        self.launchers: list[LauncherType] = []
        self.lock = threading.Lock()
        self.benchmark_failure_reasons: dict[Any, BenchmarkFailureReason] = {}
        if os.getenv("TRITON_CACHE_DIR") is None:
            os.environ["TRITON_CACHE_DIR"] = triton_cache_dir(
                self.triton_meta.get("device", 0)
            )
        log.debug("Triton cache dir: %s", os.environ["TRITON_CACHE_DIR"])

        self.size_hints = size_hints
        self.is_mix_order_reduction = self.inductor_meta.get("RSPLIT_SIZE") is not None
        self.coordesc_tuner = CoordescTuner(
            is_mm=False,
            is_native_matmul=triton_meta.get("native_matmul", False),
            is_mix_order_reduction=self.is_mix_order_reduction,
            name=self.fn.__name__,
            size_hints=size_hints,
            inductor_meta=self.inductor_meta,
        )
        self.filename = filename

        # used for profiling
        self.kernel_hash: str = ""

        # Kernels are stored in the codecache with the filename as a hash of the code.
        # We rely on this to obtain the kernel hash
        if self.filename is not None:
            base_name = os.path.basename(self.filename)
            if ".py" in base_name:
                self.kernel_hash = os.path.splitext(base_name)[0]

        self.precompile_time_taken_ns = 0
        self.autotune_time_taken_ns = 0
        # Dumps the launch configs after autotuning.
        self.dump_launch_params = (
            os.environ.get("TORCHINDUCTOR_DUMP_LAUNCH_PARAMS", "0") == "1"
        )
        self.dump_launch_tensors = (
            os.environ.get("TORCHINDUCTOR_DUMP_LAUNCH_TENSORS", "0") == "1"
        )
        self.kernels_to_dump = os.environ.get(
            "TORCHINDUCTOR_KERNELS_TO_DUMP", ""
        ).split(",")

        self.triton_interpret = os.environ.get("TRITON_INTERPRET", "0") == "1"

        self._debug_call: _TritonKernelCall | None = None
        self._profiler_ctx: _RecordFunctionFast | None = None

        # Compile-time info included in runtime logginging
        self.compile_id: CompileId | None = None
        self.is_backward = False

        # Mode for launch grid calculation
        self.grid_mode: Literal["python", "cpp"] = "python"