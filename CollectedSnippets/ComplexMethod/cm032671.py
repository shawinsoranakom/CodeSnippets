def tidy_graph(graph: nx.Graph, callback, check_attribute: bool = True):
    """
    Ensure all nodes and edges in the graph have some essential attribute.
    """

    def is_valid_item(node_attrs: dict) -> bool:
        valid_node = True
        for attr in ["description", "source_id"]:
            if attr not in node_attrs:
                valid_node = False
                break
        return valid_node

    if check_attribute:
        purged_nodes = []
        for node, node_attrs in graph.nodes(data=True):
            if not is_valid_item(node_attrs):
                purged_nodes.append(node)
        for node in purged_nodes:
            graph.remove_node(node)
        if purged_nodes and callback:
            callback(msg=f"Purged {len(purged_nodes)} nodes from graph due to missing essential attributes.")

    purged_edges = []
    for source, target, attr in graph.edges(data=True):
        if check_attribute:
            if not is_valid_item(attr):
                purged_edges.append((source, target))
        if "keywords" not in attr:
            attr["keywords"] = []
    for source, target in purged_edges:
        graph.remove_edge(source, target)
    if purged_edges and callback:
        callback(msg=f"Purged {len(purged_edges)} edges from graph due to missing essential attributes.")