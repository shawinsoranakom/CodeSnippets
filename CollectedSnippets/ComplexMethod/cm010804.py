def _extract_tangent_source_stack_traces(
    fx_g: torch.fx.GraphModule,
    fw_metadata: ViewAndMutationMeta,
) -> None:
    from .descriptors import PlainAOTOutput, TangentAOTInput

    if not fw_metadata.traced_tangents_descs:
        return

    output_node = list(fx_g.graph.nodes)[-1]
    all_outputs = output_node.args[0]

    stack_traces: list[str | None] = []
    got_one = False

    for desc in fw_metadata.traced_tangents_descs:
        stack_trace = None

        if isinstance(desc, TangentAOTInput):
            output_desc = desc.output
            if isinstance(output_desc, PlainAOTOutput) and output_desc.idx < len(
                all_outputs
            ):
                output_arg = all_outputs[output_desc.idx]
                if isinstance(output_arg, torch.fx.Node):
                    stack_trace = output_arg.meta.get("stack_trace", None)
                    got_one = True

        stack_traces.append(stack_trace)

    if got_one:
        fw_metadata.tangent_source_stack_traces = stack_traces