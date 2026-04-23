def connected_components(nodes, score_dict, link_thr):
    assert isinstance(nodes, list)
    assert all([isinstance(node, Node) for node in nodes])
    assert isinstance(score_dict, dict)
    assert isinstance(link_thr, float)

    clusters = []
    nodes = set(nodes)
    while nodes:
        node = nodes.pop()
        cluster = {node}
        node_queue = [node]
        while node_queue:
            node = node_queue.pop(0)
            neighbors = set(
                [
                    neighbor
                    for neighbor in node.links
                    if score_dict[tuple(sorted([node.ind, neighbor.ind]))] >= link_thr
                ]
            )
            neighbors.difference_update(cluster)
            nodes.difference_update(neighbors)
            cluster.update(neighbors)
            node_queue.extend(neighbors)
        clusters.append(list(cluster))
    return clusters