def color(graph: list[list[int]], max_colors: int) -> list[int]:
  
    colored_vertices = [-1] * len(graph)

    if util_color(graph, max_colors, colored_vertices, 0):
        return colored_vertices

    return []
