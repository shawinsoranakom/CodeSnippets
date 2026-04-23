def enumerate_reachable_states(
    initial_size: int,
) -> set[tuple[tuple[int, ...], tuple[int, ...]]]:
    """
    Use BFS with DP to enumerate all reachable (size, stride) states from
    a 1D contiguous tensor via valid view operations.

    We only explore states with offset=0 (you can retroactively change the offset).
    We reject states with size=0 or size=1 dimensions as they are degenerate.
    """
    # Create initial 1D contiguous tensor
    initial_tensor = torch.arange(initial_size)

    initial_state = get_state(initial_tensor)

    # Map from state to tensor for that state
    state_to_tensor: dict[tuple[tuple[int, ...], tuple[int, ...]], torch.Tensor] = {
        initial_state: initial_tensor
    }
    visited: set[tuple[tuple[int, ...], tuple[int, ...]]] = {initial_state}
    queue: deque[tuple[tuple[int, ...], tuple[int, ...]]] = deque([initial_state])

    while queue:
        state = queue.popleft()
        t = state_to_tensor[state]
        sizes, strides = state
        ndim = len(sizes)

        def add_state(new_t: torch.Tensor) -> None:
            new_state = get_state(new_t)
            sizes, strides = new_state
            # Skip if has size-0 or size-1 dimensions
            if any(s == 0 or s == 1 for s in sizes):
                return
            # Only accept states where strides are in descending order
            if list(strides) != sorted(strides, reverse=True):
                return
            if new_state not in visited:
                visited.add(new_state)
                queue.append(new_state)
                state_to_tensor[new_state] = new_t

        # 1. Unflatten: try factoring each dimension
        for dim in range(ndim):
            size = sizes[dim]
            if size <= 1:
                raise AssertionError(f"size must be > 1, got {size}")
            # Try all factorizations x * y = size where both x, y >= 2
            # We only need to check x up to size // 2 since when x > size // 2,
            # y = size // x < 2, which we reject
            for x in range(2, size // 2 + 1):
                if size % x == 0:
                    y = size // x
                    add_state(t.unflatten(dim, (x, y)))

        # 2. Slice: exhaustively check all possible slicing parameters
        for dim in range(ndim):
            size = sizes[dim]
            for start in range(size):
                for stop in range(start + 1, size + 1):
                    for step in range(1, size + 1):
                        slices = [slice(None)] * ndim
                        slices[dim] = slice(start, stop, step)
                        add_state(t[tuple(slices)])

        # 3. Flatten: merge adjacent dimensions
        for dim in range(ndim - 1):
            add_state(t.flatten(dim, dim + 1))

    return visited