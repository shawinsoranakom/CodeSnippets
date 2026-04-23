def collect_bw_donated_buffer_idxs(
    fw_module: torch.fx.GraphModule,
    bw_module: torch.fx.GraphModule,
    fw_metadata: ViewAndMutationMeta,
) -> list[int]:
    """
    Collects backward donated buffer indexes from fw_module and bw_module.
    """

    # [Note: Metadata mutation in proxy tracing]
    # node.meta["val"] is a snapshot of the tensor value when tracing a graph,
    # instead of the final state after the graph has run. node.meta["val"] is
    # not updated even if later there is a metadata mutation op.
    # See: https://github.com/pytorch/pytorch/pull/141308#issuecomment-2495798947
    #
    # Currently, metadata mutation op happens only for sacrificial parameter
    # specifically the `set_` op. This motivates banning metadata mutation from
    # proxy tracing.
    #
    # Since node.meta["val"] is used to detect donated buffer, we return an empty
    # list if there exists metadata mutation op.
    if contain_metadata_mutation_ops(fw_module) or contain_metadata_mutation_ops(
        bw_module
    ):
        return []

    fw_ins = fw_module.graph.find_nodes(op="placeholder")
    bw_outs = next(reversed(bw_module.graph.find_nodes(op="output"))).args[0]
    fw_outs = next(reversed(fw_module.graph.find_nodes(op="output"))).args[0]

    fw_ins = [
        n.meta["val"] if (hasattr(n, "meta") and "val" in n.meta) else None
        for n in fw_ins
    ]
    fw_outs = [
        n.meta["val"] if (hasattr(n, "meta") and "val" in n.meta) else None
        for n in fw_outs
    ]
    bw_outs = [
        n.meta["val"] if (hasattr(n, "meta") and "val" in n.meta) else None
        for n in bw_outs
    ]

    user_fw_outs = fw_outs[: fw_metadata.num_forward]
    saved_tensors = fw_outs[fw_metadata.tensors_saved_for_backwards_slice]

    fw_donated_buffer = collect_fw_donated_buffer_idxs(
        fw_ins,
        user_fw_outs,
        bw_outs,
        saved_tensors,
    )

    if fw_metadata.num_symints_saved_for_bw is None:
        raise AssertionError("fw_metadata.num_symints_saved_for_bw must not be None")
    return [fw_metadata.num_symints_saved_for_bw + i for i in fw_donated_buffer]