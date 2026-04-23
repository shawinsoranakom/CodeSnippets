def _apply_graph_transformation(
    transformation_fn: UserOrderingFn,
    *,
    keys_to_process: set[tuple[str, str]] | None = None,
    reregister_overrides: bool = False,
    filter_state: _FilterState | None = None,
) -> None:
    """
    Apply a transformation function to graphs and optionally reregister.

    This is the core pattern used by reorder_graphs_from_user_function and
    can be reused for other graph transformation operations.

    Args:
        transformation_fn: Function to transform each graph
        keys_to_process: Keys to process, or None for all graphs
        reregister_overrides: Whether to reregister changed graphs
        filter_state: Optional filter state for conditional registration

    Note:
        If transformation_fn raises an exception for a specific graph, that graph
        will be skipped and processing will continue with remaining graphs.
    """
    global _graphs

    # Determine which graphs to process
    target_keys = (
        keys_to_process if keys_to_process is not None else set(_graphs.keys())
    )

    # Process each graph
    for op_symbol, dispatch_key in list(target_keys):
        if (op_symbol, dispatch_key) not in _graphs:
            continue  # Skip if graph doesn't exist

        original_graph = list(_graphs[(op_symbol, dispatch_key)])

        # Apply the transformation with error handling
        try:
            new_graph = transformation_fn(op_symbol, dispatch_key, original_graph)
        except (TypeError, ValueError, AttributeError, RuntimeError):
            log.warning(
                "Graph transformation failed for %s/%s. Preserving original graph.",
                op_symbol,
                dispatch_key,
                exc_info=True,
            )
            continue
        except Exception:
            log.exception(
                "Unexpected error in graph transformation for %s/%s. Preserving original graph.",
                op_symbol,
                dispatch_key,
            )
            continue

        # Validate that the transformation returned a valid result
        if not isinstance(new_graph, list):
            log.warning(
                "Graph transformation returned invalid type %s for %s/%s. Expected list. Preserving original graph.",
                type(new_graph).__name__,
                op_symbol,
                dispatch_key,
            )
            continue

        # Update the graph
        _graphs[(op_symbol, dispatch_key)] = new_graph

        # Reregister if needed
        if reregister_overrides and _should_reregister_graph(
            original_graph, new_graph, force_reregister=False
        ):
            _cleanup_and_reregister_graph(
                op_symbol,
                dispatch_key,
                new_graph,
                filter_state=filter_state,
            )