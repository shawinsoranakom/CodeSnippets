def validate_adjacency_list(graph: list[list[int | None]]) -> None:
    """Validates the adjacency list format for the graph.

    Args:
        graph: A list of lists where each sublist contains the neighbors of a node.

    Raises:
        ValueError: If the graph is not a list of lists, or if any node has
                    invalid neighbors (e.g., out-of-range or non-integer values).

    >>> validate_adjacency_list([[1, 2], [0], [0, 1]])
    >>> validate_adjacency_list([[]])  # No neighbors, valid case
    >>> validate_adjacency_list([[1], [2], [-1]])  # Invalid neighbor
    Traceback (most recent call last):
        ...
    ValueError: Invalid neighbor -1 in node 2 adjacency list.
    """
    if not isinstance(graph, list):
        raise ValueError("Graph should be a list of lists.")

    for node_index, neighbors in enumerate(graph):
        if not isinstance(neighbors, list):
            no_neighbors_message: str = (
                f"Node {node_index} should have a list of neighbors."
            )
            raise ValueError(no_neighbors_message)
        for neighbor_index in neighbors:
            if (
                not isinstance(neighbor_index, int)
                or neighbor_index < 0
                or neighbor_index >= len(graph)
            ):
                invalid_neighbor_message: str = (
                    f"Invalid neighbor {neighbor_index} in node {node_index} "
                    f"adjacency list."
                )
                raise ValueError(invalid_neighbor_message)