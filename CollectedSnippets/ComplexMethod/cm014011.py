def collect_reachable_grad_fns(
    tensors_with_sources: list[tuple[torch.Tensor, str | None]],
    stop_at: set[torch.autograd.graph.Node] | None = None,
) -> set[torch.autograd.graph.Node]:
    """Collect all grad_fns reachable from tensors' autograd graphs.

    Performs a DFS traversal and collects all visited grad_fns.
    Optionally stops traversal nodes in stop_at set. This signals the
    autograd.grad boundary.

    Args:
        tensors_with_sources: List of (tensor, source_name) tuples to start search from.
        stop_at: Optional set of grad_fns where traversal should stop (excluded from result).

    Returns:
        Set of all reachable grad_fns.
    """
    if stop_at is None:
        stop_at = set()

    visited: set[torch.autograd.graph.Node] = set()
    stack: list[torch.autograd.graph.Node] = []

    for tensor, _ in tensors_with_sources:
        if isinstance(tensor, torch.Tensor):
            grad_fn = tensor.grad_fn
            if grad_fn is not None:
                stack.append(grad_fn)

    while stack:
        node = stack.pop()
        if node in visited:
            continue
        # Stop traversal at stop_at nodes and don't include them
        # in consumed grad_fn list.
        if node in stop_at:
            continue
        visited.add(node)
        for next_fn, _ in node.next_functions:
            if next_fn is not None:
                stack.append(next_fn)
    return visited