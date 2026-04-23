def _categorize_saved_tensors_for_backward(
    fw_module: torch.fx.GraphModule,
    bw_module: torch.fx.GraphModule,
    inner_meta: ViewAndMutationMeta,
    fw_metadata: ViewAndMutationMeta,
    num_inner_fwd_outputs: int,
) -> tuple[int, int]:
    fw_outs = next(iter(fw_module.graph.find_nodes(op="output"))).args[0]
    # we only need to bookkeep the symints that are saved for bw, not any symints
    # the user forward might have returned in its own output
    fw_outs_saved_for_bw = fw_outs[num_inner_fwd_outputs:]
    num_fw_outs_saved_for_bw = len(fw_outs_saved_for_bw)

    num_symints_saved_for_bw = 0
    num_opaque_objects_saved_for_bw = 0
    for idx, node in enumerate(fw_outs_saved_for_bw):
        if is_sym_node(node):
            num_symints_saved_for_bw += 1
        elif is_opaque_node(node):
            num_opaque_objects_saved_for_bw += 1
        elif isinstance(node, torch.fx.Node) and "val" in getattr(node, "meta", {}):
            if isinstance(node.meta["val"], FakeTensor):
                # record dynamic tensor activations
                dynamic_dims: set[int] = {
                    dim
                    for dim, size in enumerate(node.meta["val"].shape)
                    if not isinstance(size, int)
                }
                if dynamic_dims:
                    fw_metadata.dynamic_saved_tensors_idxs[idx] = dynamic_dims
            elif isinstance(node.meta["val"], (FakeScriptObject, OpaqueBase)):
                num_opaque_objects_saved_for_bw += 1

    fw_metadata.num_symints_saved_for_bw = num_symints_saved_for_bw
    fw_metadata.num_opaque_objects_saved_for_bw = num_opaque_objects_saved_for_bw
    inner_meta.num_symints_saved_for_bw = num_symints_saved_for_bw
    inner_meta.num_opaque_objects_saved_for_bw = num_opaque_objects_saved_for_bw

    # See Note [Activations with no version counter checks in eager]
    # Count tensors saved with no version counter check.
    # These are tensors that were stashed on ctx (e.g., ctx.x = x) rather than
    # via save_for_backward in an autograd.Function.
    # The partitioner sorts these to be at the end of saved_values.
    num_tensors_saved_with_no_vc_check = sum(
        1
        for node in fw_outs_saved_for_bw
        if isinstance(node, torch.fx.Node)
        and node.meta.get("saved_tensor_with_no_vc_check", False)
    )
    fw_metadata.num_tensors_saved_with_no_vc_check = num_tensors_saved_with_no_vc_check
    inner_meta.num_tensors_saved_with_no_vc_check = num_tensors_saved_with_no_vc_check

    if torch._functorch.config.donated_buffer:
        fw_metadata.bw_donated_idxs = collect_bw_donated_buffer_idxs(
            fw_module,
            bw_module,
            inner_meta,
        )
        inner_meta.bw_donated_idxs = fw_metadata.bw_donated_idxs

    return num_fw_outs_saved_for_bw, num_symints_saved_for_bw