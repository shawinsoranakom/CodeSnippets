def _serialize_graph(graph: ParseGraph) -> str:
    stack: list[Operator] = list(graph.global_scope.output_nodes)
    visited: set[Operator] = set(stack)
    edges_set = set()

    while stack:
        node = stack.pop()
        for dependency in node.input_operators():
            if dependency in graph.global_scope._nodes:
                edges_set.add((dependency, node))
                if dependency not in visited:
                    visited.add(dependency)
                    stack.append(dependency)

    nodes = []
    edges = []
    groups: dict[str, Any] = {}

    for node in visited:
        if node.trace.user_frame is None:
            continue

        user_frame = {
            "user_frame_function": node.trace.user_frame.function,
            "user_frame_filename": node.trace.user_frame.filename,
            "user_frame_line": node.trace.user_frame.line,
            "user_frame_line_number": node.trace.user_frame.line_number,
        }

        parent = f"{node.trace.user_frame.filename}:{node.trace.user_frame.line_number}"
        grandparent = node.trace.user_frame.function

        if grandparent not in groups:
            groups[grandparent] = {
                "id": f"g_{len(groups)}",
                "level": 2,
                **user_frame,
            }

        if parent not in groups:
            groups[parent] = {
                "id": f"g_{len(groups)}",
                "level": 1,
                "parent": groups[grandparent]["id"],
                **user_frame,
            }

        nodes.append(
            {
                "id": str(node.id),
                "parent": groups[parent]["id"],
                "grand_parent": groups[grandparent]["id"],
                "operator_type": node.operator_type(),
                "level": 0,
                **user_frame,
            }
        )

    for source, target in edges_set:
        edges.append(
            {
                "source": str(source.id),
                "target": str(target.id),
            }
        )

    result = {
        "nodes": nodes,
        "edges": edges,
        "groups": list(groups.values()),
    }

    return json.dumps(result)