def wrap_all_sync_nodes_with_control_deps(gm: torch.fx.GraphModule) -> None:
    """
    Single-pass wrap of all sync nodes in control_deps.

    Iterates through the graph once, accumulating per-stream node lists.
    When a sync node is encountered, it is wrapped using the accumulated deps
    for that stream, then the deps are reset to the control_deps node
    (maintaining the ordering chain for subsequent syncs on the same stream).
    """
    graph = gm.graph
    if len(graph.nodes) == 0:
        raise RuntimeError("Expected a non-empty graph")
    stream_to_nodes: dict[int | None, list[Node]] = {}
    # Maps event_index -> control_deps node that wrapped its record_event,
    # so the corresponding wait_event/synchronize_event can depend on the record.
    event_to_ctrl: dict[int, Node] = {}
    # Maps event_index -> getitem nodes threaded through record_event's control_deps,
    # so synchronize_event can thread them through to subsequent ops.
    event_to_passthrough: dict[int, list[Node]] = {}
    # Maps event_index -> stream that the event was recorded on,
    # so synchronize_event can infer its stream.
    event_to_stream: dict[int, int | None] = {}
    visited: set[Node] = set()
    found_sync = False

    # Walk the node linked-list manually so we can mutate the graph
    # (wrapping sync nodes inserts/erases nodes) without losing our place.
    node = next(iter(graph.nodes))
    while node.op != "root":
        next_node = node.next
        visited.add(node)

        if node.op == "call_function":
            if node.target in _SYNC_OPS:
                # synchronize_device and synchronize_stream block the CPU,
                # so all subsequent kernel launches are host-ordered after
                # them. Treat both as full barriers across all streams.
                if node.target in (
                    torch.ops.streams.synchronize_device.default,
                    torch.ops.streams.synchronize_stream.default,
                ):
                    all_stream_deps: list[Node] = [
                        n for nodes in stream_to_nodes.values() for n in nodes
                    ]
                    if all_stream_deps:
                        found_sync = True
                        _wrap_sync_node(gm, node, all_stream_deps, visited)
                    stream_to_nodes.clear()
                    node = next_node
                    continue

                event_index: int = node.args[0]  # type: ignore[assignment]

                # synchronize_event blocks the CPU thread, so it acts
                # as a barrier across all streams. Collect deps from every
                # stream and reset them all afterward. If the event was
                # recorded externally, thread the graph inputs through so
                # that any post-sync uses depend on the synchronize.
                if node.target is torch.ops.streams.synchronize_event.default:
                    sync_stream: int | None = event_to_stream.get(event_index)
                    all_stream_deps: list[Node] = [
                        n for nodes in stream_to_nodes.values() for n in nodes
                    ]
                    if event_index not in event_to_stream:
                        placeholders = [n for n in graph.nodes if n.op == "placeholder"]
                        deps_before_sync = [*placeholders, *all_stream_deps]
                    else:
                        deps_before_sync = all_stream_deps
                else:
                    sync_stream = node.args[1]  # type: ignore[assignment]
                    deps_before_sync = list(stream_to_nodes.get(sync_stream, ()))
                    # Nodes without explicit stream annotation (custom.stream=None)
                    # run on the current/default stream. Include them when the sync
                    # op references a stream, since the unannotated nodes are
                    # implicitly on that stream.
                    if None in stream_to_nodes and sync_stream is not None:
                        deps_before_sync.extend(stream_to_nodes[None])

                # For wait_event and synchronize_event, add a cross-event
                # dependency on the matching record_event's control_deps node
                # so they cannot be reordered before the record.
                if (
                    node.target
                    in (
                        torch.ops.streams.wait_event.default,
                        torch.ops.streams.synchronize_event.default,
                    )
                    and event_index in event_to_ctrl
                ):
                    deps_before_sync = [
                        event_to_ctrl[event_index],
                        *deps_before_sync,
                    ]

                # For synchronize_event, also include the getitem nodes
                # threaded through record_event's control_deps. This ensures
                # subsequent ops that depend on recorded values get rewired
                # through synchronize_event.
                if (
                    node.target is torch.ops.streams.synchronize_event.default
                    and event_index in event_to_passthrough
                ):
                    deps_before_sync = [
                        *deps_before_sync,
                        *event_to_passthrough[event_index],
                    ]

                if deps_before_sync:
                    found_sync = True
                    ctrl_node, passthrough = _wrap_sync_node(
                        gm, node, deps_before_sync, visited
                    )
                else:
                    ctrl_node = None
                    passthrough: list[torch.fx.Node] = []

                if node.target is torch.ops.streams.record_event.default:
                    event_to_stream[event_index] = sync_stream
                    if ctrl_node is not None:
                        event_to_ctrl[event_index] = ctrl_node
                    event_to_passthrough[event_index] = passthrough

                # Reset: ops between this sync and the next will accumulate
                # fresh. Ordering with prior ops is already enforced because
                # their uses were rewired through getitems from control_deps.
                if node.target is torch.ops.streams.synchronize_event.default:
                    stream_to_nodes.clear()
                else:
                    stream_to_nodes[sync_stream] = []
                    if None in stream_to_nodes:
                        stream_to_nodes[None] = []
            elif "val" in node.meta:
                stream = get_stream(node)
                stream_to_nodes.setdefault(stream, []).append(node)

        node = next_node

    if found_sync:
        gm.recompile()