def faces(G):
    "Return a OrderedSet of faces in G.  Where a face is a OrderedSet of vertices on that face"
    # currently limited to triangles,squares, and pentagons
    f = OrderedSet()
    for v1, edges in G.items():
        for v2 in edges:
            for v3 in G[v2]:
                if v1 == v3:
                    continue
                if v1 in G[v3]:
                    f.add(frozenset([v1, v2, v3]))
                else:
                    for v4 in G[v3]:
                        if v4 == v2:
                            continue
                        if v1 in G[v4]:
                            f.add(frozenset([v1, v2, v3, v4]))
                        else:
                            for v5 in G[v4]:
                                if v5 == v3 or v5 == v2:  # noqa: SIM109
                                    continue
                                if v1 in G[v5]:
                                    f.add(frozenset([v1, v2, v3, v4, v5]))
    return f