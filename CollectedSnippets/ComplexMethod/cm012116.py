def node_summary(snode):
    snodes = snode.get_nodes()
    if len(snodes) == 1:
        detail = ""
        if isinstance(snode.node, (ir.ExternKernelOut, ir._CollectiveKernel)):
            outs_str = f"outs:{[o.get_name() for o in snode.get_outputs()]}"
            ins_str = f"ins:{[d.name for d in snode.unmet_dependencies]}"
            detail = f" {snode.get_name()} ({snode.node.python_kernel_name})\n {outs_str}({ins_str})"
        layouts = [child.node.get_output_spec() for child in snode.get_nodes()]
        out_tensor_info = ",".join(
            [
                f" (size={layout.size}, stride={layout.stride})"
                if isinstance(layout, ir.Layout)
                else ""
                for layout in layouts
            ]
        )
        try:
            node_name = snode.node.maybe_get_name()
        except AttributeError:
            # TODO: node_summary was written without FusedSchedulerNode in mind, generally needs to be hardened
            node_name = ""
        return f"{snode.node.__class__.__name__}{detail}{out_tensor_info} ({node_name} ({snode.get_estimated_runtime():.0f} ns)"

    # Flatten the summaries for Fused/Foreach/Grouped nodes
    summaries = []
    for child_snode in snodes:
        summaries.append(node_summary(child_snode))
    return f"{snode.__class__.__name__}: {', '.join(summaries)}"