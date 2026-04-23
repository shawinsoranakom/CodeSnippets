def _fit_to_memory_budget(
    output_size: int, num_partitions: int, dtype: torch.dtype
) -> int:
    """
    Reduce partitions to fit memory budget if needed.

    Returns the maximum number of partitions that fit in memory budget.
    Returns input num_partitions if it fits, or a reduced count, or 0 if
    even min_partitions doesn't fit.
    """
    if not torch.cuda.is_available():
        return num_partitions

    try:
        _, total_memory = torch.cuda.mem_get_info()
        element_bytes = dtype.itemsize if hasattr(dtype, "itemsize") else 4
        budget = total_memory * _get_memory_budget_fraction()

        # Try reducing partitions (must be power of 2) until we fit
        current_partitions = num_partitions
        min_partitions = _get_min_partitions()
        while current_partitions >= min_partitions:
            overhead = output_size * element_bytes * (current_partitions - 1)

            if overhead <= budget:
                # Only format debug string if debug logging is enabled
                if current_partitions < num_partitions and log.isEnabledFor(
                    logging.DEBUG
                ):
                    log.debug(
                        "Reduced partitions from %d to %d to fit memory budget "
                        "(%.2fGB / %.2fGB)",
                        num_partitions,
                        current_partitions,
                        overhead / 1e9,
                        budget / 1e9,
                    )
                return current_partitions

            # Reduce by half (maintain power of 2)
            current_partitions //= 2

        # If min_partitions doesn't fit in memory, return 0
        if log.isEnabledFor(logging.DEBUG):
            overhead = output_size * element_bytes * (min_partitions - 1)
            log.debug(
                "Insufficient memory even for %d partitions: %.2fGB > %.2fGB",
                min_partitions,
                overhead / 1e9,
                budget / 1e9,
            )
        return 0

    except Exception:
        log.debug("Memory check failed, proceeding with %s", num_partitions)
        return num_partitions