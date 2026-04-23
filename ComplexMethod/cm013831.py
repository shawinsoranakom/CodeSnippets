def dynamo_timed(
    key: str,
    # TODO(masneral): Deprecate this param.
    phase_name: str | None = None,
    log_pt2_compile_event: bool = False,
    metadata: dict[str, object] | None = None,
    dynamo_compile_column_us: str | None = None,
    compile_id: CompileId | None = None,
    is_backward: bool | None = None,
    log_waitcounter: bool = False,
    waitcounter_name_override: str | None = None,
) -> Generator[Any, None, None]:
    """
    dynamo_timed is a context manager
    By wrapping a function in dynamo_timed, we can get a few things:

    1) Optionally log timings to pt2_compile_events.
    2) Optionally log timings to CompilationMetrics (dynamo_compile).
    3) Optionally log chromium events.
    4) Optionally increment a WaitCounter.
    5) Store a record in compilation_time_metrics
       For example:

        def _foo(...):
            with dynamo_timed("_foo"):
                ...

        Would show up as an entry in our timing dict:
        OrderedDict([('_foo', [0.083690, 0.23949, 3.1425e-05])])
        This is extremely useful for granular debugging.

    Although it is tempting to use dynamo_timed as a decorator, please do not.
    In its decorator form it makes cProfile traces less useful as dynamo_timed
    suddenly becomes a bottleneck for lots of function calls (as only one parent
    pointer is recorded).

    Params:
    - key: key into compile_time_metrics. If phase_name is not provided, this is
      also the event name used for pt2_compile_events logs and chromium events.
    - phase_name: Optional override for the event name.
    - log_pt2_compile_event: Whether to log a pt2 compile event internally.
    - metadata: Extra metadata to put in pt2_compile_events.
    - dynamo_compile_column_us: If provided, updates the specified CompilationMetrics
      field to be logged to dyname_compile column. We expect all columns to be _us;
      therefore, the field name must end with "_us".
    - compile_id: In the typical case, this parameter should not be needed. Use to
      supply the compile_id for those cases where we want to log a compile_id where
      it's not naturally available, e.g., for runtime autotuning.
    - is_backward: Specify forward/backward directly when not available in a
      CompileContext, e.g., during runtime autotuning.
      that support it.
    - log_waitcounter: If set, we'll log a waitcounter of the form "pytorch.dynamo_timed.{key}"
    """
    if phase_name:
        event_name = phase_name
        fn_name = key
    else:
        event_name = key
        fn_name = None

    if key not in compilation_time_metrics:
        compilation_time_metrics[key] = []

    metrics = compilation_time_metrics[key]
    event_metadata = {}
    if metadata:
        event_metadata.update(metadata)
    if fn_name:
        event_metadata.update({"fn_name": fn_name})
    if is_backward is not None:
        event_metadata.update({"is_backward": is_backward})

    chromium_log: ChromiumEventLogger = get_chromium_event_logger()
    start_ns = time.time_ns()
    chromium_log.log_event_start(
        event_name, start_ns, event_metadata, log_pt2_compile_event, compile_id
    )

    cx_mgrs: list[typing.Any] = [compile_time_record_function(f"{key} (dynamo_timed)")]
    if log_waitcounter:
        wc_name = waitcounter_name_override if waitcounter_name_override else key
        cx_mgrs.append(_WaitCounter(f"pytorch.wait_counter.{wc_name}").guard())

    is_compile_time = torch._guards.CompileContext.current_compile_id() is not None
    if dynamo_compile_column_us:
        # We're standardizing on microseconds for dynamo_compile timings.
        assert dynamo_compile_column_us.endswith("_us")

        # Track nested dynamo_timed calls that update CompilationMetrics so we can
        # bump a total duration only for the outermost metric.
        if not hasattr(_dynamo_timed_tls, "depth"):
            _dynamo_timed_tls.depth = 0
        _dynamo_timed_tls.depth += 1

        # The corresponding WaitCounters that we bump for all overheads
        if _dynamo_timed_tls.depth == 1:
            cx_mgrs.append(_WaitCounter("pytorch.wait_counter.dynamo_compile").guard())
            if not is_compile_time:
                runtime_wc = "pytorch.wait_counter.compile_runtime_overheads"
                cx_mgrs.append(_WaitCounter(runtime_wc).guard())

    try:
        with contextlib.ExitStack() as stack:
            for cx in cx_mgrs:
                stack.enter_context(cx)
            yield
    finally:
        end_ns = time.time_ns()
        time_spent_ns = end_ns - start_ns
        metrics.append(time_spent_ns / 1e9)
        chromium_log.log_event_end(
            event_name, end_ns, {}, start_ns, log_pt2_compile_event, compile_id
        )
        if dynamo_compile_column_us:
            # TODO: the events that we capture in calculate_time_spent() seem a little
            # arbitrary. Currently, it's only those fields that are present in
            # CompilationMetrics (but note that we accumulate by the associated event
            # name, not the field name in CompilationMetrics). Do we want to keep it
            # this way?
            cumulative_time_spent_ns[event_name] += time_spent_ns

            # Bump the total duration for every outer event.
            _dynamo_timed_tls.depth -= 1
            is_outer_event = _dynamo_timed_tls.depth == 0

            duration_us = time_spent_ns // 1000
            if is_compile_time:
                metrics_context = get_metrics_context()
                if metrics_context.in_progress():
                    metrics_context.increment(dynamo_compile_column_us, duration_us)
                    if is_outer_event:
                        metrics_context.increment("duration_us", duration_us)
            else:
                runtime_context = get_runtime_metrics_context()
                runtime_context.increment(dynamo_compile_column_us, duration_us)
                if is_outer_event:
                    extra = {
                        "compile_id": compile_id,
                        "is_runtime": True,
                        "is_forward": not is_backward,
                    }
                    runtime_context.increment("duration_us", duration_us, extra)