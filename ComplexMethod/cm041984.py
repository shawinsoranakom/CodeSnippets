def visualize_tree(graph, show_instructions=False, save_path=""):
    # Use a hierarchical layout for tree-like visualization
    pos = nx.spring_layout(graph, k=0.9, iterations=50)

    plt.figure(figsize=(30, 20))  # Further increase figure size for better visibility

    # Calculate node levels
    root = "0"
    levels = nx.single_source_shortest_path_length(graph, root)
    max_level = max(levels.values())

    # Adjust y-coordinates based on levels and x-coordinates to prevent overlap
    nodes_by_level = {}
    for node, level in levels.items():
        if level not in nodes_by_level:
            nodes_by_level[level] = []
        nodes_by_level[level].append(node)

    for level, nodes in nodes_by_level.items():
        y = 1 - level / max_level
        x_step = 1.0 / (len(nodes) + 1)
        for i, node in enumerate(sorted(nodes)):
            pos[node] = ((i + 1) * x_step, y)

    # Draw edges
    nx.draw_networkx_edges(graph, pos, edge_color="gray", arrows=True, arrowsize=40, width=3)

    # Draw nodes
    node_colors = [get_node_color(graph.nodes[node]) for node in graph.nodes]
    nx.draw_networkx_nodes(graph, pos, node_size=NODE_SIZE, node_color=node_colors)

    # Add labels to nodes
    labels = nx.get_node_attributes(graph, "label")
    nx.draw_networkx_labels(graph, pos, labels, font_size=NODE_FONT_SIZE)

    if show_instructions:
        # Add instructions to the right side of nodes
        instructions = nx.get_node_attributes(graph, "instruction")
        for node, (x, y) in pos.items():
            wrapped_text = textwrap.fill(instructions[node], width=30)  # Adjust width as needed
            plt.text(x + 0.05, y, wrapped_text, fontsize=15, ha="left", va="center")

    plt.title("MCTS Tree Visualization", fontsize=40)
    plt.axis("off")  # Turn off axis
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()