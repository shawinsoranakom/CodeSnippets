def merge_chunks(
    chunks: list[Any],
    chunk_spec,
):
    """
    Given a list of chunks, merge them into a single value according to
    the chunk spec.

    Args:
        chunks: list of chunks
        chunk_spec: Chunking spec for the chunks

    Returns:
        value: Merged value
    """
    # This is essentially the inverse of `split_args_kwargs_into_chunks`, so the
    # steps are similar to the steps in that function but in reverse. Given the
    # input values:
    #
    #       chunks = [
    #           ([A, [B, C_1]], D),
    #           ([A, [B, C_2]], D),
    #       ]
    #       args_spec = ([None, [None, TensorChunkSpec]], None)
    #
    # 1. Flatten the chunks according to the chunk_spec
    #
    #       chunks_flat = [
    #           ([A, B, C_1], D),
    #           ([A, B, C_2], D),
    #       ]
    #
    # 2. Rotate the nesting order such that chunks are the inner dimension
    #
    #       value_inner = ([A, B, [C_1, C_2]], D)
    #
    # 3. Concatenate sharded arguments
    #
    #       value_combined = ([A, B, C], D)
    #
    # 4. Unflatten the combined args given the spec
    #
    #       value = ([A, [B, C]], D)

    # Preliminary: flatten the chunk spec
    if chunk_spec is not None:
        spec_flattened, flatten_spec = tree_flatten(chunk_spec)
    else:
        # If chunk_spec is not provided, we will merge chunks along the default dimension (0), for all output fields
        # We obtain the output structure by flattening chunk 0 and generate the chunk_spec
        chunk0_flat, flatten_spec = tree_flatten(chunks[0])
        spec_flattened = [TensorChunkSpec(DEFAULT_CHUNK_DIM)] * len(chunk0_flat)

    # Stage 1: flatten chunks
    # chunks_flattened : [num chunks, num args]
    chunks_flattened = []

    for chunk in chunks:
        chunk_flattened, _ = tree_flatten(chunk)
        if len(chunk_flattened) != len(spec_flattened):
            raise ValueError(f"Chunk {chunk} did not match chunk spec {chunk_spec}")

        chunks_flattened.append(chunk_flattened)

    # Stage 2 and 3: Rotate nesting order s.t. chunks are inner dimension and
    #                concatenate sharded operands
    # args_flattened : [num args]
    args_flattened = []
    for arg_idx, arg in enumerate(spec_flattened):
        if isinstance(arg, TensorChunkSpec):
            partial_values = [
                chunks_flattened[chunk_idx][arg_idx]
                for chunk_idx in range(len(chunks_flattened))
            ]

            if _debug_mask_minibatches:
                # Infer size of individual chunks by running `tensor_split` again
                overall_shape = partial_values[0].shape
                for val in partial_values[1:]:
                    if not val.shape == overall_shape:
                        raise AssertionError(
                            f"Expected shape {overall_shape}, got {val.shape}"
                        )
                meta_chunks = torch.tensor_split(
                    torch.empty(*overall_shape, device="meta"),
                    sections=len(partial_values),
                    dim=arg.split_dim,
                )

                values_to_cat = []
                chunk_start_idx = 0
                if not len(partial_values) == len(meta_chunks):
                    raise AssertionError(
                        f"Expected len(partial_values) == len(meta_chunks), got {len(partial_values)} != {len(meta_chunks)}"
                    )

                for partial_value, meta_chunk in zip(
                    partial_values, meta_chunks, strict=True
                ):
                    chunk_end_idx = chunk_start_idx + meta_chunk.size(arg.split_dim)

                    slice_indices = [slice(None, None, None)] * partial_value.ndim
                    slice_indices[arg.split_dim] = slice(chunk_start_idx, chunk_end_idx)
                    sliced = partial_value[slice_indices]
                    values_to_cat.append(sliced)

                    chunk_start_idx = chunk_end_idx

            else:
                values_to_cat = partial_values

            # Validate DTensor consistency: either all values are DTensors
            # or none are. A mix indicates a bug in the pipeline stage.
            dtensor_flags = [isinstance(v, DTensor) for v in values_to_cat]
            if any(dtensor_flags):
                if not all(dtensor_flags):
                    raise AssertionError(
                        "merge_chunks: expected all values to be DTensors or "
                        "none to be DTensors, got a mix"
                    )
                # All DTensors must have matching placements.
                placements = values_to_cat[0].placements
                for i, v in enumerate(values_to_cat[1:], 1):
                    if v.placements != placements:
                        raise AssertionError(
                            f"merge_chunks: placement mismatch at chunk {i}: "
                            f"expected {placements}, got {v.placements}"
                        )
                cat_fn = local_map(
                    lambda *chunks: torch.cat(chunks, dim=arg.split_dim),
                    out_placements=(placements,),
                    in_placements=tuple(placements for _ in range(len(values_to_cat))),
                )
                args_flattened.append(cat_fn(*values_to_cat))
            else:
                args_flattened.append(torch.cat(values_to_cat, dim=arg.split_dim))
        elif isinstance(arg, _CustomReducer):
            reduced_val = arg.init_value

            for chunk_idx in range(len(chunks_flattened)):
                reduced_val = arg.reduce_fn(
                    reduced_val, chunks_flattened[chunk_idx][arg_idx]
                )

            args_flattened.append(reduced_val)
        else:
            value = chunks_flattened[0][arg_idx]
            for chunk_idx in range(1, len(chunks_flattened)):
                if not chunks_flattened[chunk_idx][arg_idx] == value:
                    raise AssertionError(
                        f"Expected {value}, got {chunks_flattened[chunk_idx][arg_idx]}"
                    )
            args_flattened.append(value)

    # Stage 4: Unflatten combined args
    return tree_unflatten(args_flattened, flatten_spec)