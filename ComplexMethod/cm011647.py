def get_fused_kernel_name(
    node_schedule: Sequence[BaseSchedulerNode],
    descriptive_names: Literal[True, "torch", "original_aten", "inductor_node"],
) -> str:
    all_origins = aggregate_origins(node_schedule)
    if descriptive_names == "original_aten":

        def get_origin_meta_str(origin):
            original_aten = origin.meta["original_aten"]
            key = ""
            if isinstance(original_aten, torch._ops.OpOverload):
                key = original_aten._overloadpacket.__name__
            elif isinstance(original_aten, torch._ops.HigherOrderOperator):
                key = str(original_aten.name())
            return key

        # Bases the kernel name off of the top-level aten operator (i.e. pre-decompositions)
        sources = [
            get_origin_meta_str(origin)
            for origin in all_origins
            if origin.op == "call_function"
            and "original_aten" in origin.meta
            and origin.meta["original_aten"] is not None
        ]
        sources = sorted(OrderedSet(sources))
    elif descriptive_names == "torch":
        # Bases the kernel name off of the top-level "torch" operator (i.e. post-dynamo graph)
        sources = []
        for origin in all_origins:
            if origin.op == "call_function":
                source_fn = None
                suffix = ""
                if "source_fn_stack" in origin.meta:
                    source_fn = origin.meta["source_fn_stack"][-1]
                elif "fwd_source_fn_stack" in origin.meta:
                    # backward nodes have "fwd_source_fn_stack" instead
                    source_fn = origin.meta["fwd_source_fn_stack"][-1]
                    suffix = "backward"
                if not source_fn:
                    continue
                if isinstance(source_fn[1], str):
                    sources.append(source_fn[1] + suffix)
                else:
                    sources.append(source_fn[1].__name__ + suffix)

        sources = sorted(OrderedSet(sources))
    elif descriptive_names == "inductor_node":
        sources = [
            origin.name for origin in all_origins if origin.op == "call_function"
        ]
    else:
        raise NotImplementedError
    return "_".join(["fused"] + sources)