def draw_graph(vertexes, edges, *, return_ascii=True):
    """Build a DAG and draw it in ASCII."""
    sug = build_sugiyama_layout(vertexes, edges)

    xlist = []
    ylist = []

    for vertex in sug.g.sV:
        xlist.extend([vertex.view.xy[0] - vertex.view.w / 2.0, vertex.view.xy[0] + vertex.view.w / 2.0])
        ylist.extend([vertex.view.xy[1], vertex.view.xy[1] + vertex.view.h])

    for edge in sug.g.sE:
        for x, y in edge.view._pts:
            xlist.append(x)
            ylist.append(y)

    minx = min(xlist)
    miny = min(ylist)
    maxx = max(xlist)
    maxy = max(ylist)

    canvas_cols = math.ceil(maxx - minx) + 1
    canvas_lines = round(maxy - miny)

    canvas = AsciiCanvas(canvas_cols, canvas_lines)

    for edge in sug.g.sE:
        if len(edge.view._pts) < MINIMUM_EDGE_VIEW_POINTS:
            msg = "edge.view._pts must have at least 2 points"
            raise ValueError(msg)
        for index in range(1, len(edge.view._pts)):
            start = edge.view._pts[index - 1]
            end = edge.view._pts[index]
            canvas.line(
                round(start[0] - minx),
                round(start[1] - miny),
                round(end[0] - minx),
                round(end[1] - miny),
                "*",
            )

    for vertex in sug.g.sV:
        x = vertex.view.xy[0] - vertex.view.w / 2.0
        y = vertex.view.xy[1]
        canvas.box(round(x - minx), round(y - miny), vertex.view.w, vertex.view.h)
        canvas.text(round(x - minx) + 1, round(y - miny) + 1, vertex.data)
    if return_ascii:
        return canvas.draws()
    canvas.draw()
    return None