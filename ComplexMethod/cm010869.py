def handle_synced_deallocation(
    graph: Graph,
    stream_to_exec_trace: dict[int | None, IndexedDict[Node, float]],
    node: Node,
    last_usage: Node,
) -> None:
    if not is_bwd_node(node):
        raise AssertionError(
            "synced allocations should only be handled on backward nodes"
        )
    if not is_bwd_node(last_usage):
        raise AssertionError(
            "synced allocations should only be handled on backward nodes"
        )
    allocating_stream = get_stream(node)
    side_stream = get_stream(last_usage)
    if allocating_stream == side_stream:
        raise AssertionError(
            "allocating and side stream should be different for synced deallocations"
        )
    if not torch.cuda.is_available():
        # fallback to record_stream in this case
        with graph.inserting_after(node):
            graph.call_function(
                torch.ops.streams.record_stream.default,
                (
                    node,
                    get_stream_or_current_stream(last_usage),
                ),
                {},
            )
        node.meta["partitioner_tag"] = "must_be_in_backward"

    allocating_stream_trace = populate_stream_timeline(
        stream_to_exec_trace, graph, allocating_stream
    )
    side_stream_trace = populate_stream_timeline(
        stream_to_exec_trace, graph, side_stream
    )

    alloc_ptr = node
    target_side_stream_time = side_stream_trace[last_usage]
    # linear search from first usage of tensor to a point in time after the side stream has finished
    while alloc_ptr is not None:
        alloc_time = allocating_stream_trace[alloc_ptr]

        if alloc_time >= target_side_stream_time:
            break
        elif alloc_time < target_side_stream_time:
            next_ptr = allocating_stream_trace.next_key(alloc_ptr)
            if next_ptr is not None:
                alloc_ptr = next_ptr
            else:
                break

    wait_event = new_event()
    record_node = insert_record_event_after_node(graph, last_usage, wait_event)
    with graph.inserting_after(max(alloc_ptr, record_node)):
        graph.call_function(
            torch.ops.streams.sync_dealloc.default,
            (wait_event, get_stream_or_current_stream(alloc_ptr), node),
            {},
        )
        node.meta["partitioner_tag"] = "must_be_in_backward"