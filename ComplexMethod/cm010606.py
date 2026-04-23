def resolve_pending_annotations() -> None:
    """Resolve pending scope index ranges into kernel annotations.

    Enumerates all graph nodes and annotates kernel/memcpy nodes whose
    indices fall within recorded scope ranges. Must be called while still
    inside the ``torch.cuda.graph()`` capture context.
    """
    global _capture_graph
    if not _pending_scopes:
        _capture_graph = None
        return

    # Get a fresh graph handle from the active capture.
    stream = _cuda_runtime.cudaStream_t(  # pyrefly: ignore[missing-attribute]
        init_value=torch.cuda.current_stream().cuda_stream
    )
    graph = _get_capture_graph(stream)
    if graph is None:
        graph = _capture_graph
    if graph is None:
        logger.warning("resolve_pending_annotations: no graph handle available")
        _pending_scopes.clear()
        return

    try:
        num = _get_node_count(graph)
        if num == 0:
            _pending_scopes.clear()
            _capture_graph = None
            return

        nodes, num = _check_cuda_bindings(
            _cuda_runtime.cudaGraphGetNodes(  # pyrefly: ignore[missing-attribute]
                graph, numNodes=num
            )
        )

        # Save capture graph ID for remap_to_exec_graph.
        global _last_capture_graph_id
        if num > 0:
            first_tid = _get_tools_id(nodes[0])
            _last_capture_graph_id = (first_tid >> 32) if first_tid else None

        annotatable = _get_annotatable_types()

        # Sort by (start, -end, -append_index). The append index encodes
        # nesting depth: inner context managers exit first, so they are
        # appended to _pending_scopes first (smaller index). Using
        # -append_index as tiebreaker ensures that for same-range scopes
        # the outer scope (larger index) sorts first and is pushed onto
        # the stack first, leaving the inner scope on top.
        sorted_scopes = sorted(
            (
                (ann, start, end, i)
                for i, (ann, start, end) in enumerate(_pending_scopes)
            ),
            key=lambda s: (s[1], -s[2], -s[3]),
        )
        scope_ptr = 0
        active_stack: list[tuple[int, Any]] = []  # (end_idx, annotation)

        for i in range(num):
            # Pop scopes whose range ended.
            while active_stack and active_stack[-1][0] <= i:
                active_stack.pop()

            # Push scopes that start at or before this index.
            while scope_ptr < len(sorted_scopes) and sorted_scopes[scope_ptr][1] <= i:
                ann, _start_idx, end_idx, _idx = sorted_scopes[scope_ptr]
                if end_idx > i:
                    active_stack.append((end_idx, ann))
                scope_ptr += 1

            if not active_stack:
                continue

            node = nodes[i]
            node_type = _check_cuda_bindings(
                _cuda_runtime.cudaGraphNodeGetType(  # pyrefly: ignore[missing-attribute]
                    node
                )
            )
            if node_type not in annotatable:
                continue

            tools_id = _get_tools_id(node)
            if tools_id is None:
                logger.warning(
                    "resolve_pending_annotations: toolsId unavailable, aborting"
                )
                _pending_scopes.clear()
                _capture_graph = None
                return

            if len(active_stack) == 1:
                _kernel_annotations[tools_id].append(active_stack[0][1])
            else:
                # Merge all active scopes into one dict. Inner scopes sit
                # on top of the stack. Iterating reversed (inner first)
                # with setdefault lets the inner scope's values win for
                # overlapping keys (e.g. name, stream) while outer scopes
                # fill in any missing keys.
                merged: dict[str, Any] = {}
                for _, ann in reversed(active_stack):
                    if isinstance(ann, dict):
                        for ak, av in ann.items():
                            merged.setdefault(ak, av)
                    else:
                        merged.setdefault("name", ann)
                _kernel_annotations[tools_id].append(merged)
    except Exception:
        logger.exception("resolve_pending_annotations failed")
    finally:
        _pending_scopes.clear()
        _capture_graph = None