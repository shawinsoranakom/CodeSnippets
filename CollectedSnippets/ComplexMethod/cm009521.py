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