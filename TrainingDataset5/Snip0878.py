def bidirectional_search(
    graph: dict[int, list[int]], start: int, goal: int
) -> list[int] | None:
    if start == goal:
        return [start]

    if start not in graph or goal not in graph:
        return None

    forward_parents: dict[int, int | None] = {start: None}
    backward_parents: dict[int, int | None] = {goal: None}

    forward_queue = deque([start])
    backward_queue = deque([goal])

    intersection = None

    while forward_queue and backward_queue and intersection is None:
        intersection = expand_search(
            graph=graph,
            queue=forward_queue,
            parents=forward_parents,
            opposite_direction_parents=backward_parents,
        )

        if intersection is not None:
            break

        intersection = expand_search(
            graph=graph,
            queue=backward_queue,
            parents=backward_parents,
            opposite_direction_parents=forward_parents,
        )

    if intersection is None:
        return None

    forward_path: list[int] = construct_path(
        current=intersection, parents=forward_parents
    )
    forward_path.reverse()

    backward_path: list[int] = construct_path(
        current=backward_parents[intersection], parents=backward_parents
    )

    return forward_path + backward_path
