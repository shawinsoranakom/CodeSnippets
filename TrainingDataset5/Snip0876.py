def expand_search(
    graph: dict[int, list[int]],
    queue: deque[int],
    parents: dict[int, int | None],
    opposite_direction_parents: dict[int, int | None],
) -> int | None:
    if not queue:
        return None

    current = queue.popleft()
    for neighbor in graph[current]:
        if neighbor in parents:
            continue

        parents[neighbor] = current
        queue.append(neighbor)

         if neighbor in opposite_direction_parents:
            return neighbor

    return None
