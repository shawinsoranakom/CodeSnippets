def operation_graph_to_networkx(graph: OperationGraph):
    """
    Convert operation graph to NetworkX graph for Python visualization.
    Requires: pip install networkx matplotlib
    """
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        print(
            "⚠️  NetworkX/Matplotlib not installed. Run: pip install networkx matplotlib"
        )
        return

    # Create directed graph
    G = nx.DiGraph()

    # Add nodes
    for node_id, node in graph.nodes.items():
        label = f"{node_id}\n{node.op_name}\ndepth {node.depth}"
        G.add_node(node_id, label=label, node=node)

    # Add edges based on the graph structure
    for node_id, node in graph.nodes.items():
        for input_node_id in node.input_nodes:
            if input_node_id in graph.nodes:  # Only add edges to nodes in the graph
                G.add_edge(input_node_id, node_id)

    # Plot
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=2, iterations=50)

    # Draw nodes with colors based on operation type
    node_colors = []
    for node_id in G.nodes():
        node = graph.nodes[node_id]
        if node.op_name.startswith("arg_"):
            node_colors.append("lightblue")
        elif node.op_name == "constant":
            node_colors.append("lightgreen")
        elif "aten" in node.op_name:
            node_colors.append("lightyellow")
        else:
            node_colors.append("lightgray")

    # Highlight root node
    node_sizes = []
    for node_id in G.nodes():
        if node_id == graph.root_node_id:
            node_sizes.append(2000)  # Larger size for root
        else:
            node_sizes.append(1500)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=20)

    # Draw labels
    labels = {
        node_id: f"{node_id}\n{graph.nodes[node_id].op_name}" for node_id in G.nodes()
    }
    nx.draw_networkx_labels(G, pos, labels, font_size=8)

    plt.title("Operation Graph Visualization")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("operation_graph_networkx.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("✓ NetworkX graph visualization saved as operation_graph_networkx.png")