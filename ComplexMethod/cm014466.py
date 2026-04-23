def create_graph(objects, *, context=None, filter=None):
    if context is None:
        context = cuda_allocation_context()
    if filter is None:
        filter = is_cuda_tensor

    objects = [obj for obj in objects if not isinstance(obj, weakref.ProxyTypes)]
    nodes = [Node(object_annotation(obj), context(obj), filter(obj), []) for obj in objects]
    node_referrers: list[list[int]] = [[] for obj in objects]

    id_to_node = {id(obj): i for i, obj in enumerate(objects)}
    for obj in objects:
        fidx = id_to_node[id(obj)]
        f = nodes[fidx]
        references = annotated_references(obj)
        for referrent in gc.get_referents(obj):
            rid = id(referrent)
            tidx = id_to_node.get(rid)
            if tidx is None:
                continue
            labels = references.get(rid, ["?"])
            node_referrers[tidx].append(fidx)
            for label in labels:
                f.referrents.append((label, tidx))

    to_search = [i for i, n in enumerate(nodes) if n.root]
    to_keep = set()
    while to_search:
        idx = to_search.pop()
        if idx in to_keep:
            continue
        to_keep.add(idx)
        referrers = node_referrers[idx]
        to_search.extend(referrers)
    id_to_filtered_id: dict[int, int] = {}
    filtered: list[Any] = []
    for i, n in enumerate(nodes):
        if i in to_keep:
            id_to_filtered_id[i] = len(id_to_filtered_id)
            filtered.append(n)
    for n in filtered:
        n.referrents[:] = [(label, id_to_filtered_id[idx])
                           for (label, idx) in n.referrents
                           if idx in id_to_filtered_id]
    return filtered