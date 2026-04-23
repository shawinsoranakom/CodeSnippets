def draw_mermaid(
    nodes: dict[str, Node],
    edges: list[Edge],
    *,
    first_node: str | None = None,
    last_node: str | None = None,
    with_styles: bool = True,
    curve_style: CurveStyle = CurveStyle.LINEAR,
    node_styles: NodeStyles | None = None,
    wrap_label_n_words: int = 9,
    frontmatter_config: dict[str, Any] | None = None,
) -> str:
    """Draws a Mermaid graph using the provided graph data.

    Args:
        nodes: List of node ids.
        edges: List of edges, object with a source, target and data.
        first_node: Id of the first node.
        last_node: Id of the last node.
        with_styles: Whether to include styles in the graph.
        curve_style: Curve style for the edges.
        node_styles: Node colors for different types.
        wrap_label_n_words: Words to wrap the edge labels.
        frontmatter_config: Mermaid frontmatter config.
            Can be used to customize theme and styles. Will be converted to YAML and
            added to the beginning of the mermaid graph.

            See more here: https://mermaid.js.org/config/configuration.html.

            Example config:

            ```python
            {
                "config": {
                    "theme": "neutral",
                    "look": "handDrawn",
                    "themeVariables": {"primaryColor": "#e2e2e2"},
                }
            }
            ```

    Returns:
        Mermaid graph syntax.

    """
    # Initialize Mermaid graph configuration
    original_frontmatter_config = frontmatter_config or {}
    original_flowchart_config = original_frontmatter_config.get("config", {}).get(
        "flowchart", {}
    )
    frontmatter_config = {
        **original_frontmatter_config,
        "config": {
            **original_frontmatter_config.get("config", {}),
            "flowchart": {**original_flowchart_config, "curve": curve_style.value},
        },
    }

    mermaid_graph = (
        (
            "---\n"
            + yaml.dump(frontmatter_config, default_flow_style=False)
            + "---\ngraph TD;\n"
        )
        if with_styles
        else "graph TD;\n"
    )
    # Group nodes by subgraph
    subgraph_nodes: dict[str, dict[str, Node]] = {}
    regular_nodes: dict[str, Node] = {}

    for key, node in nodes.items():
        if ":" in key:
            # For nodes with colons, add them only to their deepest subgraph level
            prefix = ":".join(key.split(":")[:-1])
            subgraph_nodes.setdefault(prefix, {})[key] = node
        else:
            regular_nodes[key] = node

    # Node formatting templates
    default_class_label = "default"
    format_dict = {default_class_label: "{0}({1})"}
    if first_node is not None:
        format_dict[first_node] = "{0}([{1}]):::first"
    if last_node is not None:
        format_dict[last_node] = "{0}([{1}]):::last"

    def render_node(key: str, node: Node, indent: str = "\t") -> str:
        """Helper function to render a node with consistent formatting."""
        node_name = node.name.split(":")[-1]
        label = (
            f"<p>{node_name}</p>"
            if node_name.startswith(tuple(MARKDOWN_SPECIAL_CHARS))
            and node_name.endswith(tuple(MARKDOWN_SPECIAL_CHARS))
            else node_name
        )
        if node.metadata:
            label = (
                f"{label}<hr/><small><em>"
                + "\n".join(f"{k} = {value}" for k, value in node.metadata.items())
                + "</em></small>"
            )
        node_label = format_dict.get(key, format_dict[default_class_label]).format(
            _to_safe_id(key), label
        )
        return f"{indent}{node_label}\n"

    # Add non-subgraph nodes to the graph
    if with_styles:
        for key, node in regular_nodes.items():
            mermaid_graph += render_node(key, node)

    # Group edges by their common prefixes
    edge_groups: dict[str, list[Edge]] = {}
    for edge in edges:
        src_parts = edge.source.split(":")
        tgt_parts = edge.target.split(":")
        common_prefix = ":".join(
            src for src, tgt in zip(src_parts, tgt_parts, strict=False) if src == tgt
        )
        edge_groups.setdefault(common_prefix, []).append(edge)

    seen_subgraphs = set()

    def add_subgraph(edges: list[Edge], prefix: str) -> None:
        nonlocal mermaid_graph
        self_loop = len(edges) == 1 and edges[0].source == edges[0].target
        if prefix and not self_loop:
            subgraph = prefix.rsplit(":", maxsplit=1)[-1]
            if subgraph in seen_subgraphs:
                msg = (
                    f"Found duplicate subgraph '{subgraph}' -- this likely means that "
                    "you're reusing a subgraph node with the same name. "
                    "Please adjust your graph to have subgraph nodes with unique names."
                )
                raise ValueError(msg)

            seen_subgraphs.add(subgraph)
            mermaid_graph += f"\tsubgraph {subgraph}\n"

            # Add nodes that belong to this subgraph
            if with_styles and prefix in subgraph_nodes:
                for key, node in subgraph_nodes[prefix].items():
                    mermaid_graph += render_node(key, node)

        for edge in edges:
            source, target = edge.source, edge.target

            # Add BR every wrap_label_n_words words
            if edge.data is not None:
                edge_data = edge.data
                words = str(edge_data).split()  # Split the string into words
                # Group words into chunks of wrap_label_n_words size
                if len(words) > wrap_label_n_words:
                    edge_data = "&nbsp<br>&nbsp".join(
                        " ".join(words[i : i + wrap_label_n_words])
                        for i in range(0, len(words), wrap_label_n_words)
                    )
                if edge.conditional:
                    edge_label = f" -. &nbsp;{edge_data}&nbsp; .-> "
                else:
                    edge_label = f" -- &nbsp;{edge_data}&nbsp; --> "
            else:
                edge_label = " -.-> " if edge.conditional else " --> "

            mermaid_graph += (
                f"\t{_to_safe_id(source)}{edge_label}{_to_safe_id(target)};\n"
            )

        # Recursively add nested subgraphs
        for nested_prefix, edges_ in edge_groups.items():
            if not nested_prefix.startswith(prefix + ":") or nested_prefix == prefix:
                continue
            # only go to first level subgraphs
            if ":" in nested_prefix[len(prefix) + 1 :]:
                continue
            add_subgraph(edges_, nested_prefix)

        if prefix and not self_loop:
            mermaid_graph += "\tend\n"

    # Start with the top-level edges (no common prefix)
    add_subgraph(edge_groups.get("", []), "")

    # Add remaining subgraphs with edges
    for prefix, edges_ in edge_groups.items():
        if not prefix or ":" in prefix:
            continue
        add_subgraph(edges_, prefix)
        seen_subgraphs.add(prefix)

    # Add empty subgraphs (subgraphs with no internal edges)
    if with_styles:
        for prefix, subgraph_node in subgraph_nodes.items():
            if ":" not in prefix and prefix not in seen_subgraphs:
                mermaid_graph += f"\tsubgraph {prefix}\n"

                # Add nodes that belong to this subgraph
                for key, node in subgraph_node.items():
                    mermaid_graph += render_node(key, node)

                mermaid_graph += "\tend\n"
                seen_subgraphs.add(prefix)

    # Add custom styles for nodes
    if with_styles:
        mermaid_graph += _generate_mermaid_graph_styles(node_styles or NodeStyles())
    return mermaid_graph