def __init__(
        self,
        enabled=True,
        *,
        use_cuda=False,  # Deprecated
        use_device=None,
        record_shapes=False,
        with_flops=False,
        profile_memory=False,
        with_stack=False,
        with_modules=False,
        use_kineto=False,
        use_cpu=True,
        experimental_config=None,
        acc_events=False,
        custom_trace_id_callback=None,
        post_processing_timeout_s: float | None = None,
        activity_filters: dict[ProfilerActivity, set[str]] | None = None,
    ):
        self.enabled: bool = enabled
        if not self.enabled:
            return
        self.use_cuda = use_cuda
        if self.use_cuda:
            warn(
                "The attribute `use_cuda` will be deprecated soon, "
                "please use ``use_device = 'cuda'`` instead.",
                FutureWarning,
                stacklevel=2,
            )
            self.use_device: str | None = "cuda"
        else:
            self.use_device = use_device
        # TODO Consider changing _function_events into data structure with size cap
        self._function_events: EventList | None = None
        self._old_function_events: EventList | None = None
        # Function event processing is done lazily
        self._needs_processing = False
        self.entered = False
        self.record_shapes = record_shapes
        self.with_flops = with_flops
        self.record_shapes |= self.with_flops
        self.profile_memory = profile_memory
        self.with_stack = with_stack
        self.with_modules = with_modules
        self.use_cpu = use_cpu
        self.acc_events = acc_events
        if experimental_config is None:
            experimental_config = _ExperimentalConfig()
        self.experimental_config = experimental_config
        self.kineto_results: _ProfilerResult | None = None
        self.profiling_start_time_ns = 0
        self.profiling_end_time_ns = 0
        self._stats = _ProfilerStats()
        self.custom_trace_id_callback = custom_trace_id_callback
        self.post_processing_timeout_s = post_processing_timeout_s
        self.activity_filters = activity_filters or {}
        self.trace_id = ""
        if not self.use_cpu:
            if not use_kineto:
                raise AssertionError(
                    "Device-only events supported only with Kineto (use_kineto=True)"
                )

        if self.use_device is not None:
            VALID_DEVICE_OPTIONS = ["cuda", "xpu", "mtia", "hpu"]
            if _get_privateuse1_backend_name() != "privateuseone":
                VALID_DEVICE_OPTIONS.append(_get_privateuse1_backend_name())
            if self.use_device not in VALID_DEVICE_OPTIONS:
                warn(
                    f"The {self.use_device} is not a valid device option.", stacklevel=2
                )
                self.use_device = None

            if self.use_device == "cuda" and not torch.cuda.is_available():
                warn("CUDA is not available, disabling CUDA profiling", stacklevel=2)
                self.use_cuda = False
                self.use_device = None

            if self.use_device == "xpu" and not torch.xpu.is_available():
                warn("XPU is not available, disabling XPU profiling", stacklevel=2)
                self.use_device = None

            if self.use_device == "hpu" and not (
                hasattr(torch, "hpu") and torch.hpu.is_available()
            ):
                warn("HPU is not available, disabling HPU profiling", stacklevel=2)
                self.use_device = None

        self.kineto_activities = set()
        if self.use_cpu:
            self.kineto_activities.add(ProfilerActivity.CPU)

        self.profiler_kind = ProfilerState.KINETO
        if self.use_device == "cuda":
            if not use_kineto or ProfilerActivity.CUDA not in _supported_activities():
                if not self.use_cpu:
                    raise AssertionError("Legacy CUDA profiling requires use_cpu=True")
                self.profiler_kind = ProfilerState.KINETO_GPU_FALLBACK
            else:
                self.kineto_activities.add(ProfilerActivity.CUDA)
        elif self.use_device == "xpu":
            if not (use_kineto and ProfilerActivity.XPU in _supported_activities()):
                raise AssertionError(
                    "Legacy XPU profiling is not supported. Requires use_kineto=True on XPU devices."
                )
            self.kineto_activities.add(ProfilerActivity.XPU)
        elif self.use_device == "mtia":
            if not (use_kineto and ProfilerActivity.MTIA in _supported_activities()):
                raise AssertionError(
                    "Legacy MTIA profiling is not supported. Requires use_kineto=True on MTIA devices."
                )
            self.kineto_activities.add(ProfilerActivity.MTIA)
        elif self.use_device == "hpu":
            if not (use_kineto and ProfilerActivity.HPU in _supported_activities()):
                raise AssertionError(
                    "Legacy HPU profiling is not supported. Requires use_kineto=True on HPU devices."
                )
            self.kineto_activities.add(ProfilerActivity.HPU)
        elif self.use_device is not None and self.use_device != "privateuseone":
            if use_kineto:
                # Native tracing mode: use KINETO_PRIVATEUSE1 with registered IActivityProfiler
                self.profiler_kind = ProfilerState.KINETO_PRIVATEUSE1
                if ProfilerActivity.PrivateUse1 in _supported_activities():
                    self.kineto_activities.add(ProfilerActivity.PrivateUse1)
            else:
                # Marker-only mode: use fallback state
                if not self.use_cpu:
                    raise AssertionError(
                        "Legacy privateuse1 profiling requires use_cpu=True"
                    )
                self.profiler_kind = ProfilerState.KINETO_PRIVATEUSE1_FALLBACK

        if len(self.kineto_activities) == 0:
            raise AssertionError("No activities specified for the profiler")

        if (
            self.post_processing_timeout_s is not None
            and self.post_processing_timeout_s < 0
        ):
            raise ValueError("post_processing_timeout_s must be non-negative")