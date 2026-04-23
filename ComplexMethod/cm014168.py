def collect_intermediate_outputs(
    tx: "InstructionTranslator",
    subtracer: "SubgraphTracer",
    graph_output_vts: Sequence[VariableTracker],
    filter_aliased_intermediates: bool = False,
) -> list[VariableTracker]:
    extra_outputs = []
    existing_out_proxies = {vt.as_proxy() for vt in graph_output_vts}

    # Build the aliasing tracker if we're filtering
    tracker = None
    if filter_aliased_intermediates:
        tracker = StorageAliasingTracker()
        tracker.collect_from_inputs(tx)
        tracker.collect_from_outputs(graph_output_vts)

    for out in subtracer.tracked_proxyable_vt:
        proxy = out.as_proxy()

        # Skip if already in output
        if proxy in existing_out_proxies:
            continue

        # TODO floats are not supported in HOP input/output
        if isinstance(out, SymNodeVariable) and out.python_type() is float:
            continue

        if not filter_aliased_intermediates:
            extra_outputs.append(out)
        else:
            # Filter out intermediates that alias with inputs or outputs.
            # This is needed for HOPs like invoke_subgraph that don't support aliasing.
            assert tracker is not None
            if tracker.check_and_track(proxy.node):
                extra_outputs.append(out)
            else:
                taint_filtered_vt(out)

    return extra_outputs