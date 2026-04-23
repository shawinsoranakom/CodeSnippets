def graph_propagation(edges, scores, text_comps, edge_len_thr=50.0):
    assert edges.ndim == 2
    assert edges.shape[1] == 2
    assert edges.shape[0] == scores.shape[0]
    assert text_comps.ndim == 2
    assert isinstance(edge_len_thr, float)

    edges = np.sort(edges, axis=1)
    score_dict = {}
    for i, edge in enumerate(edges):
        if text_comps is not None:
            box1 = text_comps[edge[0], :8].reshape(4, 2)
            box2 = text_comps[edge[1], :8].reshape(4, 2)
            center1 = np.mean(box1, axis=0)
            center2 = np.mean(box2, axis=0)
            distance = norm(center1 - center2)
            if distance > edge_len_thr:
                scores[i] = 0
        if (edge[0], edge[1]) in score_dict:
            score_dict[edge[0], edge[1]] = 0.5 * (
                score_dict[edge[0], edge[1]] + scores[i]
            )
        else:
            score_dict[edge[0], edge[1]] = scores[i]

    nodes = np.sort(np.unique(edges.flatten()))
    mapping = -1 * np.ones((np.max(nodes) + 1), dtype=np.int32)
    mapping[nodes] = np.arange(nodes.shape[0])
    order_inds = mapping[edges]
    vertices = [Node(node) for node in nodes]
    for ind in order_inds:
        vertices[ind[0]].add_link(vertices[ind[1]])

    return vertices, score_dict