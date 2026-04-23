def _compute_indices_of_inps_to_detach(
    bw_module: torch.fx.GraphModule,
    maybe_subclass_meta: SubclassMeta | None,
    inner_meta: ViewAndMutationMeta,
    fw_metadata: ViewAndMutationMeta,
) -> list[int]:
    # TODO: we should apply the below "detach inputs if their gradients are statically known to be None"
    # optimization even if we have subclass inputs/outputs (we do not handle this today).
    # Computing which our our inputs get None gradients is a bit more complicated,
    # if any of our inputs are subclasses. Why?
    # (a) we need to make sure that we call .detach() on the input subclasses, since autograd sees subclasses.
    # (b) The grad_outputs that we AOT computed in our backward graph are the desugared tensor tensors,
    #     so we need to figure out which subclass fw inputs they map to.
    if maybe_subclass_meta is not None:
        return []

    indices_of_inps_to_detach: list[int] = []

    # reversed() since we expect output at end of graph
    bw_output = next(reversed(bw_module.graph.find_nodes(op="output")))
    bw_outs = bw_output.args[0]

    num_backward_tokens = inner_meta.num_backward_tokens
    expected_bw_outs = (
        len(fw_metadata.input_info)
        + inner_meta.num_outputs_rng_offset
        + num_backward_tokens
    )
    if len(bw_outs) != expected_bw_outs:
        raise AssertionError(
            f"expected len(bw_outs) == {expected_bw_outs}, got {len(bw_outs)}"
        )

    bw_outs_no_rng_no_tokens = bw_outs
    if (inner_meta.num_outputs_rng_offset + num_backward_tokens) > 0:
        bw_outs_no_rng_no_tokens = bw_outs[
            : -(inner_meta.num_outputs_rng_offset + num_backward_tokens)
        ]
    if len(bw_outs_no_rng_no_tokens) != len(fw_metadata.input_info):
        raise AssertionError(
            f"expected len(bw_outs_no_rng_no_tokens) == {len(fw_metadata.input_info)}, "
            f"got {len(bw_outs_no_rng_no_tokens)}"
        )

    for i, bw_out in enumerate(bw_outs_no_rng_no_tokens):
        # If our input experiences a metadata mutation inside the graph (e.g. set_()),
        # we *must* not detach, otherwise it will be the detach'd input that gets the metadata mutation
        metadata_mutation_in_graph = (
            fw_metadata.input_info[i].mutation_type == MutationType.MUTATED_IN_GRAPH
            and fw_metadata.input_info[i].mutates_storage_metadata
        )
        is_non_leaf = (
            fw_metadata.input_info[i].requires_grad
            and not fw_metadata.input_info[i].is_leaf
        )
        if bw_out is None and not metadata_mutation_in_graph and is_non_leaf:
            indices_of_inps_to_detach.append(i)

    return indices_of_inps_to_detach