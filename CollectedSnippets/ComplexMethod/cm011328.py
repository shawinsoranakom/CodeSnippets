def _validate_global_plan(global_plan: list[SavePlan], metadata: Metadata) -> list[str]:
    """Validate the global plan and return a list of error messages (empty if valid)."""
    errors: list[str] = []
    for key, value in metadata.state_dict_metadata.items():
        if isinstance(value, BytesStorageMetadata):
            continue
        if len(value.size) == 0:
            continue
        chunks = value.chunks
        chunks_volume = 0
        for chunk in chunks:
            # Compute the volume
            if not _check_box_bounds(value.size, chunk):
                msg = (
                    f"key:{key} has out of bounds chunk: "
                    f"tensor-size:{value.size} chunk: {chunk}"
                )
                logger.warning(msg)
                errors.append(msg)
            chunks_volume += math.prod(chunk.sizes)

        if len(chunks) > 1:
            dims = len(value.size)
            sweep_dim = max(range(dims), default=0, key=lambda d: value.size[d])
            sorted_indices = sorted(
                range(len(chunks)),
                key=lambda idx: (
                    chunks[idx].offsets[sweep_dim],
                    *(chunks[idx].offsets[d] for d in range(dims)),
                ),
            )
            active: list[tuple[int, int]] = []
            for idx in sorted_indices:
                current = chunks[idx]
                start = current.offsets[sweep_dim]
                end = start + current.sizes[sweep_dim]

                cutoff = bisect_right(active, (start, sys.maxsize))
                if cutoff:
                    del active[:cutoff]

                for _, other_idx in active:
                    other = chunks[other_idx]
                    if _check_box_overlap(current, other):
                        msg = f"key:{key} has overlapping chunks: {current} {other}"
                        logger.warning(msg)
                        errors.append(msg)

                insort(active, (end, idx))

        # Check whether combined chunk cover the whole tensor
        tensor_volume = math.prod(value.size)
        if len(global_plan) > 1 and chunks_volume != tensor_volume:
            msg = (
                f"key:{key} invalid fill tensor-volume: "
                f"{tensor_volume} chunks-volume: {chunks_volume}"
            )
            logger.warning(msg)
            errors.append(msg)

    return errors