def construct_reverse_graph(roots: list[Node]) -> dict[Node, list[Node]]:
    q: collections.deque[Node] = collections.deque()
    root_seen: set[Node] = set()
    reverse_edges_dict: dict[Node, list[Node]] = collections.defaultdict(list)
    for node in roots:
        if node is not None and node not in root_seen:
            q.append(node)
            root_seen.add(node)
    while q:
        node = q.popleft()
        for fn, _ in node.next_functions:
            if fn is not None:
                if len(reverse_edges_dict[fn]) == 0:
                    q.append(fn)
                reverse_edges_dict[fn].append(node)
    return reverse_edges_dict