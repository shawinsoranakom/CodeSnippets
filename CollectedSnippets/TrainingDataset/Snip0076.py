
def util_color(
    graph: list[list[int]], max_colors: int, colored_vertices: list[int], index: int
) -> bool:

    if index == len(graph):
        return True

    for i in range(max_colors):
        if valid_coloring(graph[index], colored_vertices, i):
            colored_vertices[index] = i
            if util_color(graph, max_colors, colored_vertices, index + 1):
                return True
            colored_vertices[index] = -1
    return False
