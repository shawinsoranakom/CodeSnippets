def set_kernel_post_grad_provenance_tracing(
    node_schedule: Sequence[BaseSchedulerNode] | ExternKernel,
    kernel_name: str,
    is_extern: bool = False,
) -> int | None:
    """
    Set the mapping between `kernel_name` and the post_grad nodes in `node_schedule`.

    Returns a unique int debug handler for each call to this function.
    """

    if config.trace.provenance_tracking_level == 0:
        return None

    try:
        from .codegen.simd_kernel_features import DisableReduction, EnableReduction

        global _inductor_triton_kernel_to_post_grad_node_info
        global _inductor_kernel_stack_trace
        global _inductor_kernel_provenance_debug_handle

        _inductor_kernel_provenance_debug_handle += 1
        stack_traces: list[str] = []
        kernel_name = f"{kernel_name}:{_inductor_kernel_provenance_debug_handle}"
        if is_extern:
            assert isinstance(node_schedule, ExternKernel)
            curr_node_info = _inductor_triton_kernel_to_post_grad_node_info.setdefault(
                kernel_name, []
            )
            # 'origins' on IR nodes gives what FX IR nodes contributed to any given fused kernel.
            # "origin_node" is more precise and says that the contents of this node corresponds
            # EXACTLY to the output of a particular FX node, but it's not always available
            if node_schedule.origin_node:
                origin_node_name = node_schedule.origin_node.name
                if origin_node_name not in curr_node_info:
                    curr_node_info.append(origin_node_name)
            else:
                curr_node_info.extend(
                    origin.name
                    for origin in node_schedule.origins
                    if origin.name not in curr_node_info
                )
            stack_traces = list(node_schedule.get_stack_traces())
        else:
            assert isinstance(node_schedule, list)
            stack_traces_set: OrderedSet[str] = OrderedSet()
            for snode in node_schedule:
                if snode not in (EnableReduction, DisableReduction):
                    if snode.node is not None:
                        curr_node_info = (
                            _inductor_triton_kernel_to_post_grad_node_info.setdefault(
                                kernel_name, []
                            )
                        )
                        # pyrefly: ignore [missing-attribute]
                        stack_traces_set.update(snode.node.get_stack_traces())
                        curr_node_info.extend(
                            origin.name
                            # pyrefly: ignore [missing-attribute]
                            for origin in snode.node.origins
                            if origin.name not in curr_node_info
                        )
            stack_traces = list(stack_traces_set)
        _inductor_kernel_stack_trace.setdefault(kernel_name, []).extend(stack_traces)
        return _inductor_kernel_provenance_debug_handle
    except Exception as e:
        # Since this is just debugging, it should never interfere with regular
        # program execution, so we use this try-except to guard against any error
        signpost_event(
            "inductor",
            "provenance_tracking_error",
            {
                "function": "set_kernel_post_grad_provenance_tracing",
                "error_msg": str(e),
                "stack_trace": traceback.format_exc(),
            },
        )
        return None