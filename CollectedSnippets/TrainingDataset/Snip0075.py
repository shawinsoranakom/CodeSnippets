def valid_coloring(
    neighbours: list[int], colored_vertices: list[int], color: int
) -> bool:
    
    return not any(
        neighbour == 1 and colored_vertices[i] == color
        for i, neighbour in enumerate(neighbours)
    )
