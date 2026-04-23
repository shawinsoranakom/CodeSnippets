def remove_dupe_metadata(
    m: ViewAndMutationMeta,
    keep_arg_mask: list[bool],
    add_dupe_map: list[int],
) -> ViewAndMutationMeta:
    if len(m.input_info) != len(keep_arg_mask):
        raise AssertionError(
            f"len(m.input_info)={len(m.input_info)} != len(keep_arg_mask)={len(keep_arg_mask)}"
        )
    # Easy invariant: the first argument should never be a dupe (it will be kept)
    if len(keep_arg_mask) == 0 or not keep_arg_mask[0]:
        raise AssertionError(
            "keep_arg_mask must be non-empty and keep_arg_mask[0] must be True"
        )

    # Filter dupe'd mutated inputs out of traced_tangents
    num_data_mutations = len([x for x in m.input_info if x.mutates_data])
    other_traced_tangents = m.traced_tangents[num_data_mutations:]
    inp_traced_tangents = m.traced_tangents[:num_data_mutations]
    other_traced_tangents_descs = m.traced_tangents_descs[num_data_mutations:]
    inp_traced_tangents_descs = m.traced_tangents_descs[:num_data_mutations]
    filtered_inp_traced_tangents = [
        # See Note [Tangents memory format]
        x
        for i, x in enumerate(inp_traced_tangents)
        if keep_arg_mask[m.mutated_inp_runtime_indices[i]]
    ]
    filtered_inp_traced_tangents_descs = [
        x_desc
        for i, x_desc in enumerate(inp_traced_tangents_descs)
        if keep_arg_mask[m.mutated_inp_runtime_indices[i]]
    ]
    traced_tangents = filtered_inp_traced_tangents + other_traced_tangents
    traced_tangents_descs = (
        filtered_inp_traced_tangents_descs + other_traced_tangents_descs
    )

    if m.subclass_tangent_meta is None:
        raise AssertionError("m.subclass_tangent_meta must not be None")
    subclass_tangent_meta = [
        PlainTensorMeta(
            0, memory_format=MemoryFormatMeta(memory_format=torch.contiguous_format)
        )
    ] * len(filtered_inp_traced_tangents) + m.subclass_tangent_meta[num_data_mutations:]

    return ViewAndMutationMeta(
        input_info=[x for i, x in enumerate(m.input_info) if keep_arg_mask[i]],
        # For outputs that are views of inputs, we store the index of the input that the output
        # was generated from. Need to update that index to account for removed dupes.
        output_info=[
            OutputAliasInfo(
                output_type=o.output_type,
                raw_type=o.raw_type,
                dynamic_dims=o.dynamic_dims,
                base_idx=None if o.base_idx is None else add_dupe_map[o.base_idx],
                requires_grad=o.requires_grad,
                requires_grad_for_backward=o.requires_grad_for_backward,
                view_meta_sequence=o.view_meta_sequence,
            )
            for o in m.output_info
        ],
        num_intermediate_bases=m.num_intermediate_bases,
        keep_input_mutations=m.keep_input_mutations,
        traced_tangents=traced_tangents,
        traced_tangents_descs=traced_tangents_descs,
        # We are guaranteed not to get here, since dupes are not supported today with subclass inputs.
        subclass_inp_meta=[],
        subclass_fw_graph_out_meta=[],
        subclass_tangent_meta=subclass_tangent_meta,
    )