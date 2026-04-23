def build_json(root, graph) -> dict:
    if "node" not in root.data:
        # If the root node has no "node" key, then it has only one child,
        # which is the target of the single outgoing edge
        edge = root.edges[0]
        local_nodes = [edge.target]
    else:
        # Otherwise, find all children whose type matches the type
        # specified in the template
        node_type = root.node_type
        local_nodes = graph.get_nodes_with_target(root)

    if len(local_nodes) == 1:
        return build_json(local_nodes[0], graph)
    # Build a dictionary from the template
    template = root.data["node"]["template"]
    final_dict = template.copy()

    for key in final_dict:
        if key == "_type":
            continue

        value = final_dict[key]
        node_type = value["type"]

        if "value" in value and value["value"] is not None:
            # If the value is specified, use it
            value = value["value"]
        elif "dict" in node_type:
            # If the value is a dictionary, create an empty dictionary
            value = {}
        else:
            # Otherwise, recursively build the child nodes
            children = []
            for local_node in local_nodes:
                node_children = graph.get_children_by_node_type(local_node, node_type)
                children.extend(node_children)

            if value["required"] and not children:
                msg = f"No child with type {node_type} found"
                raise ValueError(msg)
            values = [build_json(child, graph) for child in children]
            value = (
                list(values) if value["list"] else next(iter(values), None)  # type: ignore[arg-type]
            )
        final_dict[key] = value

    return final_dict