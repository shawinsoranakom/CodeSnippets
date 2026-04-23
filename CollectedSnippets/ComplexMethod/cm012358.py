def propagate_single_node(
    queue: Queue, fwd_filter: dict[Node, bool], bwd_filter: dict[Node, bool], node: Node
) -> None:  # type: ignore[type-arg]
    log.debug("Propagate_single_node: %s", node.format_node())

    if node.op != "call_function":
        raise CantChunk(
            "Chunker can only propagate chunking metadata thru call_function nodes"
        )

    target = node.target
    if log.isEnabledFor(logging.DEBUG):
        log.debug("Before propagation, the node has the following chunking meta:")
        format_node_with_chunking_meta(node, True)

    if not isinstance(target, torch._ops.OpOverload) or target not in propagate_rules:
        raise CantChunk(
            f"Missing propagation rule for target {target}: {node.format_node()}"
        )

    status = propagate_rules[target](node)

    if log.isEnabledFor(logging.DEBUG):
        log.debug("After propagation, the node has the following chunking meta:")
        format_node_with_chunking_meta(node, True)

    if status == PropagateStatus.FAIL:
        raise CantChunk(f"Propagate rule for {target} fail: {node.format_node()}")
    elif status == PropagateStatus.SUCCEED_WITH_CHANGE:
        # propagate to used nodes
        for arg in get_args_of_node_type(node):
            # don't propagate back thru a placeholder node
            if arg.op == "placeholder":
                if "tangent" in arg.target:  # type: ignore[operator]
                    # we have a separate pass to propagate scale_by information fwd.
                    set_chunking_meta(arg, scale_by=arg)
            elif bwd_filter[arg]:
                _enqueue(queue, arg)

        # propagate to user nodes
        if fwd_filter[node]:
            for user in node.users:
                _enqueue(queue, user)
    else:
        assert status == PropagateStatus.SUCCEED_NO_CHANGE, (
            f"status type {type(status)}, value {status}"
        )