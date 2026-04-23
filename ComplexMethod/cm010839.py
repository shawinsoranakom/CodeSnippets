def compute_inner_mutated_inp_indices_from_subclass_meta(
    fw_metadata: ViewAndMutationMeta,
    inner_metadata: ViewAndMutationMeta,
) -> list[int]:
    # Note: [Recomputing subclass mutation handling]
    #
    # Generally, if a subclass requires grad, its components will not require grad.
    # But for the purposes of tracking returned tensors, we should treat those component
    # tensors as if they require grad.
    #
    # For example, if the subclass tensor requires grad and will be mutated in a way that
    # requires us to handle the mutation outside of the graph, we need to return it
    # from the forward graph. The inner_meta data won't consider the component tensors
    # as if they need to be returned, because they don't require grad; but really, we
    # should handle those tensors the same way we handle the subclass tensor itself; i.e.
    # if we'd include the subclass tensor as part of the outputs, then we should also
    # include the component tensors.
    #
    # To do this, we patch num_mutated_inp_runtime_indices below by expanding the inputs
    # from the outer subclass tensors and propagating

    updated_input_info = []
    inner_idx = 0
    if not fw_metadata.subclass_inp_meta:
        # Sometimes we don't have subclass info, e.g. synthetic_base codepaths
        return inner_metadata.mutated_inp_runtime_indices
    if len(fw_metadata.subclass_inp_meta) != len(fw_metadata.input_info):
        raise AssertionError(
            f"subclass_inp_meta length ({len(fw_metadata.subclass_inp_meta)}) != input_info length ({len(fw_metadata.input_info)})"
        )
    for outer_idx, inp_meta in enumerate(fw_metadata.subclass_inp_meta):
        if isinstance(inp_meta, PlainTensorMeta):
            if outer_idx >= len(fw_metadata.input_info):
                raise AssertionError(
                    f"outer_idx ({outer_idx}) >= len(fw_metadata.input_info) ({len(fw_metadata.input_info)})"
                )
            if inner_metadata is not None:
                if inner_idx >= len(inner_metadata.input_info):
                    raise AssertionError(
                        f"inner_idx ({inner_idx}) >= len(inner_metadata.input_info) ({len(inner_metadata.input_info)})"
                    )
                if (
                    inner_metadata.input_info[inner_idx]
                    != fw_metadata.input_info[outer_idx]
                ):
                    raise AssertionError(
                        f"input_info mismatch at inner_idx={inner_idx}, outer_idx={outer_idx}: "
                        f"{inner_metadata.input_info[inner_idx]} != {fw_metadata.input_info[outer_idx]}"
                    )
            updated_input_info.append(fw_metadata.input_info[outer_idx])
            inner_idx += 1
        else:
            if inp_meta.original_subclass is None:
                raise AssertionError(
                    "inp_meta.original_subclass must not be None for SubclassCreationMeta"
                )
            for _ in range(inp_meta.arg_count):
                updated_input_info.append(fw_metadata.input_info[outer_idx])
                inner_idx += 1
    if inner_metadata is not None:
        if len(inner_metadata.input_info) != len(updated_input_info):
            raise AssertionError(
                f"inner_metadata.input_info length ({len(inner_metadata.input_info)}) "
                f"!= updated_input_info length ({len(updated_input_info)})"
            )

    return [
        i
        for i, inp in enumerate(updated_input_info)
        if inp.mutation_type == MutationType.MUTATED_OUT_GRAPH
    ]