def create_read_items_for_chunk_list(
    fqn: str,
    checkpoint_md: TensorStorageMetadata,
    local_chunks: list[ChunkStorageMetadata],
) -> list[ReadItem]:
    """
    Create a list of ``ReadItem`` based on the checkpoint and local chunks.

    This applies the resharding algorithm and computes the reads needed
    to satisfy ``local_chunks`` with a checkpoint described by ``checkpoint_md``.

    Args:
        fqn (str) : The state_dict FQN to pass to ``ReadItem``.
        checkpoint_md (TensorStorageMetadata): metadata for a given tensor
            from a checkpoint.
        local_chunks (List[ChunkStorageMetadata]): Local chunks that needs to be
            loaded.

    Returns:
        A list of ``ReadItem`` that will satisfy all input chunks.
    """
    read_items: list[ReadItem] = []
    saved_chunks = checkpoint_md.chunks

    if not local_chunks or not saved_chunks:
        return read_items

    num_dims = len(local_chunks[0].offsets)

    # Find sweep dimension (dimension with largest extent for better pruning)
    sweep_dim = 0
    if num_dims > 1:
        max_size = 0
        for dim in range(num_dims):
            dim_size = max(
                chunk.offsets[dim] + chunk.sizes[dim]
                for chunk in itertools.chain(local_chunks, saved_chunks)
            )
            if dim_size > max_size:
                max_size = dim_size
                sweep_dim = dim

    # Pre-compute bounds: (start, end) for each chunk in sweep dimension
    # For 0-d tensors, use (0, 1) so all chunks overlap in the sweep line
    if num_dims == 0:
        saved_bounds = [(0, 1)] * len(saved_chunks)
        local_bounds = [(0, 1)] * len(local_chunks)
    else:
        saved_bounds = [
            (c.offsets[sweep_dim], c.offsets[sweep_dim] + c.sizes[sweep_dim])
            for c in saved_chunks
        ]
        local_bounds = [
            (c.offsets[sweep_dim], c.offsets[sweep_dim] + c.sizes[sweep_dim])
            for c in local_chunks
        ]

    saved_sorted_indices = sorted(
        range(len(saved_chunks)),
        key=lambda idx: saved_bounds[idx][0],
    )
    local_sorted_indices = sorted(
        range(len(local_chunks)),
        key=lambda idx: local_bounds[idx][0],
    )

    active_saved: list[tuple[int, int]] = []
    saved_ptr = 0
    num_saved = len(saved_sorted_indices)

    for local_idx in local_sorted_indices:
        local_chunk = local_chunks[local_idx]
        local_start, local_end = local_bounds[local_idx]

        cutoff = bisect_right(active_saved, (local_start, -1))
        if cutoff:
            del active_saved[:cutoff]

        while saved_ptr < num_saved:
            storage_idx = saved_sorted_indices[saved_ptr]
            storage_chunk = saved_chunks[storage_idx]
            saved_start, saved_end = saved_bounds[storage_idx]

            if saved_start >= local_end:
                break

            insort(active_saved, (saved_end, storage_idx))
            saved_ptr += 1

        for _, storage_idx in active_saved:
            storage_chunk = saved_chunks[storage_idx]
            if not _check_shard_metadata_pair_overlap(local_chunk, storage_chunk):
                continue

            storage_offsets = []
            dest_offsets = []
            lengths = []
            for (
                _dim,
                offset_for_saved_tensor,
                offset_for_current_tensor,
                length,
            ) in _shards_get_overlap_region_wrt_saved_tensor(
                saved_shard=storage_chunk, current_shard=local_chunk
            ):
                storage_offsets.append(offset_for_saved_tensor)
                dest_offsets.append(offset_for_current_tensor)
                lengths.append(length)

            read_items.append(
                _create_read_item_for_tensor(
                    dest_index=MetadataIndex(fqn, local_chunk.offsets, local_idx),
                    dest_offsets=dest_offsets,
                    storage_index=MetadataIndex(
                        fqn, storage_chunk.offsets, storage_idx
                    ),
                    storage_offsets=storage_offsets,
                    lengths=lengths,
                )
            )
    return read_items