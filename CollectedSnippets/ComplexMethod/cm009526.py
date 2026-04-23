def draw_ascii(vertices: Mapping[str, str], edges: Sequence[LangEdge]) -> str:
    """Build a DAG and draw it in ASCII.

    Args:
        vertices: list of graph vertices.
        edges: list of graph edges.

    Raises:
        ValueError: if the canvas dimensions are invalid or if
            edge coordinates are invalid.

    Returns:
        ASCII representation

    Example:
        ```python
        from langchain_core.runnables.graph_ascii import draw_ascii

        vertices = {1: "1", 2: "2", 3: "3", 4: "4"}
        edges = [
            (source, target, None, None)
            for source, target in [(1, 2), (2, 3), (2, 4), (1, 4)]
        ]


        print(draw_ascii(vertices, edges))
        ```

        ```txt

                 +---+
                 | 1 |
                 +---+
                 *    *
                *     *
               *       *
            +---+       *
            | 2 |       *
            +---+**     *
              *    **   *
              *      ** *
              *        **
            +---+     +---+
            | 3 |     | 4 |
            +---+     +---+
        ```
    """
    # NOTE: coordinates might me negative, so we need to shift
    # everything to the positive plane before we actually draw it.
    xlist: list[float] = []
    ylist: list[float] = []

    sug = _build_sugiyama_layout(vertices, edges)

    for vertex in sug.g.sV:
        # NOTE: moving boxes w/2 to the left
        xlist.extend(
            (
                vertex.view.xy[0] - vertex.view.w / 2.0,
                vertex.view.xy[0] + vertex.view.w / 2.0,
            )
        )
        ylist.extend((vertex.view.xy[1], vertex.view.xy[1] + vertex.view.h))

    for edge in sug.g.sE:
        for x, y in edge.view.pts:
            xlist.append(x)
            ylist.append(y)

    minx = min(xlist)
    miny = min(ylist)
    maxx = max(xlist)
    maxy = max(ylist)

    canvas_cols = math.ceil(math.ceil(maxx) - math.floor(minx)) + 1
    canvas_lines = round(maxy - miny)

    canvas = AsciiCanvas(canvas_cols, canvas_lines)

    # NOTE: first draw edges so that node boxes could overwrite them
    for edge in sug.g.sE:
        if len(edge.view.pts) <= 1:
            msg = "Not enough points to draw an edge"
            raise ValueError(msg)
        for index in range(1, len(edge.view.pts)):
            start = edge.view.pts[index - 1]
            end = edge.view.pts[index]

            start_x = round(start[0] - minx)
            start_y = round(start[1] - miny)
            end_x = round(end[0] - minx)
            end_y = round(end[1] - miny)

            if start_x < 0 or start_y < 0 or end_x < 0 or end_y < 0:
                msg = (
                    "Invalid edge coordinates: "
                    f"start_x={start_x}, "
                    f"start_y={start_y}, "
                    f"end_x={end_x}, "
                    f"end_y={end_y}"
                )
                raise ValueError(msg)

            canvas.line(start_x, start_y, end_x, end_y, "." if edge.data else "*")

    for vertex in sug.g.sV:
        # NOTE: moving boxes w/2 to the left
        x = vertex.view.xy[0] - vertex.view.w / 2.0
        y = vertex.view.xy[1]

        canvas.box(
            round(x - minx),
            round(y - miny),
            vertex.view.w,
            vertex.view.h,
        )

        canvas.text(round(x - minx) + 1, round(y - miny) + 1, vertex.data)

    return canvas.draw()