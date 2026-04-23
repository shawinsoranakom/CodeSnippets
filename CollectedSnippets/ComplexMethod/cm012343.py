def validate_match(match: Match) -> bool:
    """Check if pattern match should be optimized for scatter."""
    output_node = match.output_node()
    if not output_node or not hasattr(output_node, "args") or len(output_node.args) < 4:
        return False

    # Only apply when accumulating
    if output_node.args[3] is not True:
        log.debug("Skipping: accumulate=False")
        return False

    # Extract metadata
    input_node = output_node.args[0]
    indices_arg = output_node.args[1]

    # Validate input_node is an FX Node
    if not isinstance(input_node, fx.Node):
        return False

    scatter_dim, index_node = _extract_scatter_dim_and_index(indices_arg)
    if scatter_dim is None or index_node is None:
        return False

    # Get tensor shapes and validate
    input_meta = _get_tensor_meta(input_node)
    index_meta = _get_tensor_meta(index_node)
    if not input_meta or not index_meta:
        return False

    # Skip unsupported cases
    if isinstance(input_meta["numel"], torch.SymInt) or isinstance(
        index_meta["numel"], torch.SymInt
    ):
        log.debug("Skipping: dynamic shapes not supported")
        return False

    if input_meta["dtype"] == torch.bool or index_meta["dtype"] == torch.bool:
        log.debug("Skipping: bool dtype not supported")
        return False

    if scatter_dim >= len(input_meta["shape"]):
        log.debug("Skipping: scatter dim %d out of bounds", scatter_dim)
        return False

    # Calculate optimal partitions and check memory
    output_size = input_meta["numel"]
    index_size = index_meta["numel"]

    # Safety check (also done in _estimate_optimal_partitions)
    if output_size == 0 or index_size == 0:
        return False

    contention_ratio = index_size / output_size

    # Check minimum index size threshold
    min_index_size = getattr(config, "partitioned_scatter_min_index_size", 4096)
    if index_size < min_index_size:
        log.debug(
            "Skipping: index size %d below threshold %d", index_size, min_index_size
        )
        return False

    # Get optimal partitions and adjust for memory constraints
    num_partitions = _estimate_optimal_partitions(output_size, index_size)
    num_partitions = _fit_to_memory_budget(
        output_size, num_partitions, input_meta["dtype"]
    )

    # If reduced to < min partitions, optimization not worthwhile
    if num_partitions < _get_min_partitions():
        log.debug("Skipping: insufficient memory for minimum partitions")
        return False

    # Store optimization parameters for replacement
    match._num_partitions = num_partitions  # type: ignore[attr-defined]
    match._scatter_dim = scatter_dim  # type: ignore[attr-defined]
    match._index_node = index_node  # type: ignore[attr-defined]

    log.debug(
        "Applying optimization: %d partitions, dim=%d, contention=%.2f, "
        "output_size=%d, index_size=%d",
        num_partitions,
        scatter_dim,
        contention_ratio,
        output_size,
        index_size,
    )

    return True