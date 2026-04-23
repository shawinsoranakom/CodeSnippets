def trace_structured(
    name: str,
    # NB: metadata expected to be dict so adding more info is forward compatible
    # Tuple[str, int] is a special case for string interning
    metadata_fn: Callable[[], dict[str, Any] | tuple[str, int]] = dict,
    *,
    payload_fn: Callable[[], str | object | None] = lambda: None,
    suppress_context: bool = False,
    expect_trace_id: bool = True,  # Whether or not we expect to have a current trace id
    record_logging_overhead: bool = True,  # Whether or not to record the time spent on structured logging
    compile_id: CompileId | None = None,  # Optional if unavailable in the trace
) -> None:
    """
    metadata is an arbitrary JSON compatible struct, but it's expected to not be
    too long (e.g., less than 1MB)

    payload is an arbitrary string, which can be arbitrarily long (but expected to have
    newlines so no lines are too long)
    """
    reserved_names = [
        "rank",
        "compiled_autograd_id",
        "frame_id",
        "frame_compile_id",
        "attempt",
        "severity",
        "timestamp",
        "pathname",
        "thread",
    ]
    if name in reserved_names:
        raise AssertionError(f"name {name!r} is reserved and cannot be used")
    if not callable(metadata_fn):
        raise AssertionError(
            f"metadata_fn should be callable, but got {type(metadata_fn)}"
        )
    if not callable(payload_fn):
        raise AssertionError(
            f"payload_fn should be callable, but got {type(payload_fn)}"
        )
    # trace_log never propagates and is ALWAYS DEBUG, so also check that there
    # are handlers instead of checking the log level
    if trace_log.handlers:
        start_time = time.time_ns()
        record: dict[str, object] = {}
        record[name] = metadata_fn()
        if not suppress_context:
            # TODO: Actually, the rank probably should just be emitted once at
            # the top, and not repeatedly spammed in all the logs, since it
            # never changes and we assume no interleaving
            if dist.is_available() and dist.is_initialized():
                record["rank"] = dist.get_rank()

            trace_id = torch._guards.CompileContext.current_trace_id()
            if expect_trace_id and trace_id is None and compile_id is None:
                # Record the stack of the log call to better diagnose why we
                # don't have a frame id for it
                record["stack"] = torch._logging.structured.from_traceback(
                    CapturedTraceback.extract(skip=1).summary()
                )
            else:
                cid = trace_id.compile_id if trace_id else compile_id
                if cid is not None:
                    if cid.compiled_autograd_id is not None:
                        record["compiled_autograd_id"] = cid.compiled_autograd_id
                    if cid.frame_id is not None:
                        record["frame_id"] = cid.frame_id
                    if cid.frame_compile_id is not None:
                        record["frame_compile_id"] = cid.frame_compile_id
                if trace_id:
                    record["attempt"] = trace_id.attempt

        payload = payload_fn()
        if payload is not None:
            if not isinstance(payload, str):
                if isinstance(payload, list):
                    # special case to look better
                    payload = "[\n" + ",\n".join(json.dumps(i) for i in payload) + "\n]"
                else:

                    def json_default(obj):
                        # Sets aren't json serializable
                        if isinstance(obj, set):
                            return list(obj)
                        raise TypeError(
                            f"Object of type {type(obj)} is not JSON serializable"
                        )

                    # force newlines so we are unlikely to overflow line limit
                    payload = json.dumps(payload, default=json_default, indent=0)
            h = hashlib.md5(usedforsecurity=False)
            h.update(payload.encode("utf-8"))
            record["has_payload"] = h.hexdigest()
        trace_log.debug(
            "", extra={"metadata": record, "payload": payload}, stacklevel=2
        )
        log_trace_structured_event(name, record)

        if record_logging_overhead:
            # Convert to seconds from nanoseconds, add it to the frame compile total
            structured_logging_overhead_s = (time.time_ns() - start_time) / 1e9
            add_structured_logging_overhead(structured_logging_overhead_s)