def _parse_legacy_records(thread_records):
    def _get_record_key(record):
        """Return a tuple for correlating start and end records in `_parse_legacy_records`."""
        return (record.handle(), record.node_id())

    start_record = None
    functions = []

    # '__start_profile' is not guaranteed to be first, so we must find it here
    for record in itertools.chain.from_iterable(thread_records):
        name = record.name()
        if start_record is None and name == "__start_profile":
            start_record = record

    if start_record is None or start_record.is_remote():
        raise AssertionError("Expected a valid local start_record")

    for thread_record_list in thread_records:
        # accumulated memory allocations per handle
        cpu_memory_allocs = {}
        cuda_memory_allocs = {}
        # ranges per handle
        range_starts = {}

        filtered_handles = set()
        prev_record = None
        for record in thread_record_list:
            record_key = _get_record_key(record)
            if _filter_name(record.name()) or record_key in filtered_handles:
                filtered_handles.add(record_key)
                continue

            if record.kind() == "push":
                # workaround to reduce double logging from operator
                # wrappers and redispatch
                if prev_record is not None:
                    duplicate = (
                        prev_record.name() == record.name()
                        and prev_record.kind() == record.kind()
                        and prev_record.node_id() == record.node_id()
                    )
                    if duplicate:
                        filtered_handles.add(record_key)
                        continue

                range_starts[record_key] = record
                cpu_memory_allocs[record_key] = 0
                cuda_memory_allocs[record_key] = 0
            elif record.kind() == "pop":
                if record_key not in range_starts:
                    raise AssertionError(
                        f"Expected record with key {record_key} to exist in range_starts. "
                        "This means that the pop event did not have a corresponding push."
                    )

                start = range_starts[record_key]

                cpu_memory_usage = cpu_memory_allocs[record_key]
                cuda_memory_usage = cuda_memory_allocs[record_key]
                is_async = start.is_async() or (start.thread_id() != record.thread_id())
                is_remote_event = record.is_remote()
                start_flops = start.flops()

                fe = FunctionEvent(
                    id=record.handle(),
                    node_id=record.node_id(),
                    name=_rewrite_name(name=start.name(), with_wildcard=True),
                    trace_name=_rewrite_name(name=start.name(), with_wildcard=False),
                    thread=start.thread_id(),
                    start_us=start_record.cpu_elapsed_us(start),
                    end_us=start_record.cpu_elapsed_us(record),
                    fwd_thread=start.fwd_thread_id(),
                    input_shapes=start.shapes(),
                    stack=[
                        entry for entry in start.stack() if _filter_stack_entry(entry)
                    ],
                    scope=start.scope(),
                    use_device="cuda" if start.has_cuda() else None,
                    cpu_memory_usage=cpu_memory_usage,
                    device_memory_usage=cuda_memory_usage,
                    is_async=is_async,
                    is_remote=is_remote_event,
                    sequence_nr=start.sequence_nr(),
                    device_type=DeviceType.CPU,
                    is_legacy=True,
                    flops=start_flops,
                )
                # note: async events have only cpu total time
                if not is_async and start.has_cuda():
                    duration = start.cuda_elapsed_us(record)
                    if duration > 0:
                        fe.append_kernel(start.name(), start.device(), duration)
                functions.append(fe)
                del range_starts[record_key]
                del cpu_memory_allocs[record_key]
                del cuda_memory_allocs[record_key]
            elif record.kind() == "memory_alloc":
                num_open_handles_cpu = len(cpu_memory_allocs)
                num_open_handles_cuda = len(cuda_memory_allocs)
                if num_open_handles_cpu != num_open_handles_cuda:
                    raise AssertionError(
                        f"Expected CPU and CUDA memory allocation handles to match, "
                        f"but got {num_open_handles_cpu} CPU and {num_open_handles_cuda} CUDA"
                    )
                for handle in cpu_memory_allocs:
                    cpu_memory_allocs[handle] += record.cpu_memory_usage()
                for handle in cuda_memory_allocs:
                    cuda_memory_allocs[handle] += record.cuda_memory_usage()
                if num_open_handles_cpu == 0:
                    # output event as a top-level memory event
                    fe = FunctionEvent(
                        id=0,
                        name=MEMORY_EVENT_NAME,
                        trace_name=None,
                        thread=0,
                        start_us=0,
                        end_us=0,
                        stack=[],
                        cpu_memory_usage=record.cpu_memory_usage(),
                        device_memory_usage=record.cuda_memory_usage(),
                        is_legacy=True,
                    )
                    functions.append(fe)
            prev_record = record

    # Sort functions by start time then by end time ascending.
    # This ensures that--in the case of nested events which
    # have the same start time (which may happen due to the
    # granularity of the given clock tick)--we always show
    # the outermost nested call first. This adds stability
    # in how FunctionEvents appear
    functions.sort(key=lambda evt: [evt.time_range.start, -evt.time_range.end])
    return functions