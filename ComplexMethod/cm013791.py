def __init__(
        self,
        *,
        activities: Iterable[ProfilerActivity | dict[ProfilerActivity, list[str]]]
        | None = None,
        schedule: Callable[[int], ProfilerAction] | None = None,
        on_trace_ready: Callable[..., Any] | None = None,
        record_shapes: bool = False,
        profile_memory: bool = False,
        with_stack: bool = False,
        with_flops: bool = False,
        with_modules: bool = False,
        experimental_config: _ExperimentalConfig | None = None,
        execution_trace_observer: _ITraceObserver | None = None,
        acc_events: bool = False,
        # deprecated:
        use_cuda: bool | None = None,
        custom_trace_id_callback: Callable[[], str] | None = None,
        post_processing_timeout_s: float | None = None,
    ) -> None:
        # Extract activities for the use_cuda deprecation check.
        if activities is not None:
            activities_set: set[ProfilerActivity] = set()
            for item in activities:
                if isinstance(item, ProfilerActivity):
                    activities_set.add(item)
                elif isinstance(item, dict):
                    activities_set.update(item.keys())
        else:
            activities_set = supported_activities()
        if use_cuda is not None:
            warn(
                "`use_cuda` is deprecated, use `activities` argument instead",
                FutureWarning,
                stacklevel=2,
            )
            if use_cuda:
                activities_set.add(ProfilerActivity.CUDA)
            elif ProfilerActivity.CUDA in activities_set:
                activities_set.remove(ProfilerActivity.CUDA)
        if len(activities_set) == 0:
            raise AssertionError("No valid profiler activities found")

        super().__init__(
            activities=activities,
            record_shapes=record_shapes,
            profile_memory=profile_memory,
            with_stack=with_stack,
            with_flops=with_flops,
            with_modules=with_modules,
            experimental_config=experimental_config,
            execution_trace_observer=execution_trace_observer
            or ExecutionTraceObserver.build_execution_trace_obs_from_env(),
            acc_events=acc_events,
            custom_trace_id_callback=custom_trace_id_callback,
            post_processing_timeout_s=post_processing_timeout_s,
        )

        if schedule:
            self.schedule = schedule
            # add step markers into the trace and table view
            self.record_steps = True
        else:
            self.schedule = _default_schedule_fn
            self.record_steps = False
        self.on_trace_ready = on_trace_ready
        self.step_num = 0
        self.current_action = self.schedule(self.step_num)
        self.step_rec_fn: prof.record_function | None = None

        self.action_map: dict[
            tuple[ProfilerAction, ProfilerAction | None], list[Any]
        ] = {
            # key is (prev_action, current_action), value is action list corresponding to the state pair.
            (ProfilerAction.NONE, ProfilerAction.NONE): [],
            (ProfilerAction.NONE, ProfilerAction.WARMUP): [self.prepare_trace],
            (ProfilerAction.NONE, ProfilerAction.RECORD): [
                self.prepare_trace,
                self.start_trace,
            ],
            (ProfilerAction.NONE, ProfilerAction.RECORD_AND_SAVE): [
                self.prepare_trace,
                self.start_trace,
            ],
            (ProfilerAction.WARMUP, ProfilerAction.NONE): [
                partial(warn, "Incorrect schedule: WARMUP followed by NONE"),
                self.start_trace,
                self.stop_trace,
            ],
            (ProfilerAction.WARMUP, ProfilerAction.WARMUP): [],
            (ProfilerAction.WARMUP, ProfilerAction.RECORD): [self.start_trace],
            (ProfilerAction.WARMUP, ProfilerAction.RECORD_AND_SAVE): [self.start_trace],
            (ProfilerAction.RECORD, ProfilerAction.NONE): [
                partial(warn, "Incorrect schedule: RECORD followed by NONE"),
                self.stop_trace,
            ],
            (ProfilerAction.RECORD, ProfilerAction.WARMUP): [
                partial(warn, "Incorrect schedule: RECORD followed by WARMUP"),
                self.stop_trace,
            ],
            (ProfilerAction.RECORD, ProfilerAction.RECORD): [],
            (ProfilerAction.RECORD, ProfilerAction.RECORD_AND_SAVE): [],
            (ProfilerAction.RECORD_AND_SAVE, ProfilerAction.NONE): [
                self.stop_trace,
                self._trace_ready,
            ],
            (ProfilerAction.RECORD_AND_SAVE, ProfilerAction.WARMUP): [
                self.stop_trace,
                self._trace_ready,
                self.prepare_trace,
            ],
            (ProfilerAction.RECORD_AND_SAVE, ProfilerAction.RECORD): [
                self.stop_trace,
                self._trace_ready,
                self.prepare_trace,
                self.start_trace,
            ],
            (ProfilerAction.RECORD_AND_SAVE, ProfilerAction.RECORD_AND_SAVE): [
                self.stop_trace,
                self._trace_ready,
                self.prepare_trace,
                self.start_trace,
            ],
            # used for exit action
            (ProfilerAction.WARMUP, None): [self.start_trace, self.stop_trace],
            (ProfilerAction.RECORD, None): [self.stop_trace, self._trace_ready],
            (ProfilerAction.RECORD_AND_SAVE, None): [
                self.stop_trace,
                self._trace_ready,
            ],
        }
        # Start tracking increments to profiler step, this will be used
        # by Kineto
        prof.KinetoStepTracker.init_step_count(PROFILER_STEP_NAME)