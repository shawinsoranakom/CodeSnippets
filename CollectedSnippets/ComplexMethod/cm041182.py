def populate_graph(graph: networkx.DiGraph, root: Shape):
    stack: list[Shape] = [root]
    visited: set[str] = set()

    while stack:
        cur = stack.pop()
        if cur is None:
            continue

        if cur.name in visited:
            continue

        visited.add(cur.name)
        graph.add_node(cur.name, shape=cur)

        if isinstance(cur, ListShape):
            graph.add_edge(cur.name, cur.member.name)
            stack.append(cur.member)
        elif isinstance(cur, StructureShape):
            for member in cur.members.values():
                stack.append(member)
                graph.add_edge(cur.name, member.name)
        elif isinstance(cur, MapShape):
            stack.append(cur.key)
            stack.append(cur.value)
            graph.add_edge(cur.name, cur.key.name)
            graph.add_edge(cur.name, cur.value.name)

        else:  # leaf types (int, string, bool, ...)
            pass