def create_synthetic_base_metadata(
    m: ViewAndMutationMeta,
    # Maps each outer argument idx to its inner idx (or, if this outer arg is generated from a
    # synthetic base, you get a tuple of (i, TensorMeta), telling you the base tensor idx, and view metadata)
    synthetic_base_info: list[int | tuple[int, torch.Tensor]],
    outer_args: list[Any],
    inner_args: list[Any],
    inner_args_desc: list[AOTInput],
) -> tuple[ViewAndMutationMeta, list[int]]:
    # maps inner arg indices to outer arg indices
    synthetic_base_to_indices: dict[int, list[int]] = {}
    for inner_idx in range(len(inner_args)):
        outer_aliased_indices_of_current_base_arg = [
            outer_idx
            for outer_idx, inner_idx_or_tuple in enumerate(synthetic_base_info)
            if (isinstance(inner_idx_or_tuple, int) and inner_idx_or_tuple == inner_idx)
            or (
                isinstance(inner_idx_or_tuple, tuple)
                and inner_idx_or_tuple[0] == inner_idx
            )
        ]
        synthetic_base_to_indices[inner_idx] = outer_aliased_indices_of_current_base_arg

    # given the requires_grad info on mutated inputs,
    # generate the requires_grad info on those same mutated inputs, but after constructing synthetic bases.
    # pyrefly: ignore [implicit-any]
    input_infos = []
    for outer_indices in synthetic_base_to_indices.values():
        # leaf-ness should be all-or-nothing for aliased tensor.
        # (aka if "a" and "b" are views, then a.is_leaf == b.is_leaf)
        any_leaf = any(m.input_info[x].is_leaf for x in outer_indices)
        all_leaf = all(m.input_info[x].is_leaf for x in outer_indices)
        if any_leaf != all_leaf:
            raise AssertionError(
                f"any_leaf={any_leaf} != all_leaf={all_leaf} for outer_indices={outer_indices}"
            )

        mutates_data = (
            True
            if len(outer_indices) > 1
            else m.input_info[outer_indices[0]].mutates_data
        )
        mutates_metadata = (
            False
            if len(outer_indices) > 1
            else m.input_info[outer_indices[0]].mutates_metadata
        )
        requires_grad = any(m.input_info[x].requires_grad for x in outer_indices)
        mutations_under_no_grad_or_inference_mode = all(
            m.input_info[x].mutations_under_no_grad_or_inference_mode
            for x in outer_indices
        )

        mutation_inductor_storage_resize = all(
            m.input_info[x].mutation_inductor_storage_resize for x in outer_indices
        )

        inpt_info = InputAliasInfo(
            # If len(outer_indices) > 1, then this input is a synthetic base.
            # The invariant is that to the rest of aot autograd, synthetic bases only show up if
            # one of their aliases gets a data mutation. And if any of their aliases get metadata
            # mutations, they will be hidden from the rest of aot autograd.
            mutates_data=mutates_data,
            mutates_metadata=mutates_metadata,
            mutations_hidden_from_autograd=all(
                m.input_info[x].mutations_hidden_from_autograd for x in outer_indices
            ),
            mutates_storage_metadata=(
                False
                if len(outer_indices) > 1
                else m.input_info[outer_indices[0]].mutates_storage_metadata
            ),
            mutations_under_no_grad_or_inference_mode=mutations_under_no_grad_or_inference_mode,
            mutation_inductor_storage_resize=mutation_inductor_storage_resize,
            is_leaf=any_leaf,
            requires_grad=requires_grad,
            keep_input_mutations=m.keep_input_mutations,
        )
        input_infos.append(inpt_info)

    # Find any inputs that fulfill the following criteria:
    # (1) They are part of a synthetic base (because they alias another input,
    #      and at least one input experiences a data mutation)
    # (2) They experience a metadata mutation
    outer_aliased_arg_idx_with_metadata_mutations = [
        outer_idx
        for outer_idx, inpt_info in enumerate(m.input_info)
        if inpt_info.mutates_metadata
        and not isinstance(synthetic_base_info[outer_idx], int)
    ]

    # grab the original requires grad info on the outputs, except the ones from the mutated inputs
    input_metadata_output_info = [
        OutputAliasInfo(
            output_type=OutputType.alias_of_input,
            raw_type=FunctionalTensor,
            dynamic_dims={
                i
                for i, s in enumerate(outer_args[outer_idx].shape)
                if not is_concrete_int(s)
            },
            base_idx=synthetic_base_info[outer_idx][0],  # type: ignore[index]
            requires_grad=(requires_grad := outer_args[outer_idx].requires_grad),
            requires_grad_for_backward=requires_grad,
        )
        for outer_idx in outer_aliased_arg_idx_with_metadata_mutations
    ]
    existing_output_infos = []
    for o in m.output_info:
        new_base_idx = (
            None
            if o.base_idx is None
            else (
                synthetic_base_info[o.base_idx]
                if isinstance(synthetic_base_info[o.base_idx], int)
                else synthetic_base_info[o.base_idx][0]  # type: ignore[index]
            )
        )
        # If base_idx is changed for OutputType.is_input, we need to update the output type to reflect the change
        new_output_type = (
            OutputType.alias_of_input
            if o.output_type == OutputType.is_input and o.base_idx != new_base_idx
            else o.output_type
        )
        existing_output_infos.append(
            OutputAliasInfo(
                output_type=new_output_type,
                raw_type=o.raw_type,
                dynamic_dims=o.dynamic_dims,
                # Map the input idx pre-synthetic-bases to the new idx post-synthetic-bases
                base_idx=new_base_idx,  # type: ignore[arg-type]
                requires_grad=o.requires_grad,
                requires_grad_for_backward=o.requires_grad_for_backward,
                view_meta_sequence=o.view_meta_sequence,
            )
        )

    inner_mutated_tangents_and_memory_formats = [
        # See Note [Tangents memory format]
        (
            coerce_tangent_and_suggest_memory_format(x),
            TangentAOTInput(InputMutationAOTOutput(x_desc)),
        )
        for inner_idx, (x, x_desc) in enumerate(zip(inner_args, inner_args_desc))
        if input_infos[inner_idx].mutates_data and input_infos[inner_idx].requires_grad
    ]
    inner_mutated_tangents = [
        x[0][0] for x in inner_mutated_tangents_and_memory_formats
    ]
    inner_mutated_tangents_descs = [
        x[1] for x in inner_mutated_tangents_and_memory_formats
    ]
    inner_mutated_tangents_memory_formats = [
        x[0][1] for x in inner_mutated_tangents_and_memory_formats
    ]

    output_info = existing_output_infos + input_metadata_output_info
    # Regenerate traced tangents to include mutated inputs including synthetic bases
    traced_tangents = (
        inner_mutated_tangents + m.traced_tangents[len(inner_mutated_tangents) :]
    )
    traced_tangents_descs = (
        inner_mutated_tangents_descs
        + m.traced_tangents_descs[len(inner_mutated_tangents) :]
    )
    if m.subclass_tangent_meta is None:
        raise AssertionError("m.subclass_tangent_meta must not be None")
    subclass_tangent_meta = [
        # pyrefly: ignore[bad-argument-type]
        PlainTensorMeta(0, memory_format=x)
        for x in inner_mutated_tangents_memory_formats
    ] + m.subclass_tangent_meta[len(inner_mutated_tangents) :]

    return (
        ViewAndMutationMeta(
            input_info=input_infos,
            output_info=output_info,
            num_intermediate_bases=m.num_intermediate_bases,
            keep_input_mutations=m.keep_input_mutations,
            traced_tangents=traced_tangents,
            traced_tangents_descs=traced_tangents_descs,
            # We are guaranteed not to get here, since synthetic_base codepaths are not supported today with subclass inputs.
            subclass_inp_meta=[],
            subclass_fw_graph_out_meta=[],
            subclass_tangent_meta=subclass_tangent_meta,
        ),
        outer_aliased_arg_idx_with_metadata_mutations,
    )