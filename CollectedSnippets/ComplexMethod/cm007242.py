def build_sugiyama_layout(vertexes, edges):
    vertexes = {v: GrandalfVertex(v) for v in vertexes}
    edges = [GrandalfEdge(vertexes[s], vertexes[e]) for s, e in edges]
    graph = GrandalfGraph(vertexes.values(), edges)

    for vertex in vertexes.values():
        vertex.view = VertexViewer(vertex.data)

    minw = min(v.view.w for v in vertexes.values())

    for edge in edges:
        edge.view = EdgeViewer()

    sug = SugiyamaLayout(graph.C[0])
    roots = [v for v in sug.g.sV if len(v.e_in()) == 0]
    sug.init_all(roots=roots, optimize=True)

    sug.yspace = VertexViewer.HEIGHT
    sug.xspace = minw
    sug.route_edge = route_with_lines

    sug.draw()
    return sug