def profile_inline_call(
    output: OutputGraph,
    code: types.CodeType,
    get_inline_depth: Callable[[], int],
) -> Generator[None, None, None]:
    """
    Context manager for profiling inline calls.

    Args:
        output: The OutputGraph containing profiler_state
        code: The code object being inlined (for timing metadata)
        get_inline_depth: Callable that returns inline_depth (called after work completes)

    Yields:
        None (profiling happens around the with block)
    """
    if not config.dynamo_profiler:
        yield
        return

    if output.profiler_state is None:
        output.profiler_state = DynamoProfilerState()

    caller_info = output.profiler_state.get_current_caller()
    call_stack = output.profiler_state.get_call_stack()

    output.profiler_state.push(
        code.co_name, code.co_filename, code.co_firstlineno, time.time_ns()
    )

    trace_success = False
    try:
        yield
        trace_success = True
    finally:
        stack_entry = output.profiler_state.pop()
        trace_end_ns = time.time_ns()

        if trace_success and stack_entry is not None:
            inline_depth = get_inline_depth()
            cumtime_ns = trace_end_ns - stack_entry.start_time_ns
            tottime_ns = cumtime_ns - stack_entry.child_time_ns

            timing = FunctionTraceTiming(
                func_name=stack_entry.func_name,
                filename=stack_entry.filename,
                firstlineno=stack_entry.firstlineno,
                cumtime_ns=cumtime_ns,
                tottime_ns=tottime_ns,
                bytecode_count=len(code.co_code),
                inline_depth=inline_depth,
                caller_func_name=caller_info[0] if caller_info else None,
                caller_filename=caller_info[1] if caller_info else None,
                caller_firstlineno=caller_info[2] if caller_info else None,
                is_primitive_call=stack_entry.is_primitive_call,
                call_stack=call_stack,
            )
            output.profiler_state.record_timing(timing)
            output.profiler_state.add_child_time(cumtime_ns)