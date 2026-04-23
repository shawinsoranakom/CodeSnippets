def operation_graph_to_dot(
    graph: OperationGraph, title: str = "Operation Graph"
) -> str:
    """
    Convert an operation graph to Graphviz DOT format for visualization.

    Args:
        graph: OperationGraph instance
        title: Title for the graph

    Returns:
        DOT format string
    """
    dot_lines = [
        "digraph OperationGraph {",
        f'    label="{title}";',
        "    rankdir=TB;",  # Top to bottom layout
        "    node [shape=box, style=filled, fontsize=10];",
        "    edge [fontsize=8];",
        "",
    ]

    # Add nodes with styling based on operation type
    for node_id, node in graph.nodes.items():
        # Choose color and shape based on operation type
        if node.op_name.startswith("arg_"):
            color = "lightblue"
            shape = "ellipse"
        elif node.op_name == "constant":
            color = "lightgreen"
            shape = "ellipse"
        elif "aten" in node.op_name:
            color = "lightyellow"
            shape = "box"
        else:
            color = "lightgray"
            shape = "box"

        # Create comprehensive label
        if node.op_name.startswith("arg_"):
            label_parts = [node.op_name]
        else:
            label_parts = [node_id, node.op_name, f"depth {node.depth}"]

        if hasattr(node.output_spec, "dtype"):
            dtype_str = str(node.output_spec.dtype).replace("torch.", "")
            label_parts.append(dtype_str)

        # Only add size for TensorSpec, not ScalarSpec
        if isinstance(node.output_spec, TensorSpec) and node.output_spec.size:
            size_str = "x".join(map(str, node.output_spec.size))
            label_parts.append(f"size {size_str}")

        label = "\\n".join(label_parts)

        # Special highlighting for root node
        extra_style = ""
        if node_id == graph.root_node_id:
            extra_style = ", penwidth=3, color=red"

        dot_lines.append(
            f'    {node_id} [label="{label}", fillcolor="{color}", shape="{shape}"{extra_style}];'
        )

    dot_lines.append("")

    # Add edges based on the graph structure
    for node_id, node in graph.nodes.items():
        for i, input_node_id in enumerate(node.input_nodes):
            # Add edge from input node to current node with input position label
            edge_label = f"input_{i}"
            dot_lines.append(
                f'    {input_node_id} -> {node_id} [label="{edge_label}"];'
            )

    dot_lines.extend(
        [
            "",
            "    // Legend",
            "    subgraph cluster_legend {",
            '        label="Legend";',
            "        style=filled;",
            "        fillcolor=white;",
            '        legend_arg [label="arg", fillcolor=lightblue, shape=ellipse];',
            '        legend_const [label="constant", fillcolor=lightgreen, shape=ellipse];',
            '        legend_aten [label="aten ops", fillcolor=lightyellow, shape=box];',
            '        legend_root [label="root", fillcolor=orange, shape=box, penwidth=3, color=red];',
            "    }",
            "}",
        ]
    )

    return "\n".join(dot_lines)