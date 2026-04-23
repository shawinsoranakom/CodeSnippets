def _validate_graph_structure(graph: BaseGraph):
        """Validate graph structure (links, connections, etc.)"""
        node_map = {v.id: v for v in graph.nodes}

        def is_static_output_block(nid: str) -> bool:
            return node_map[nid].block.static_output

        # Links: links are connected and the connected pin data type are compatible.
        for link in graph.links:
            source = (link.source_id, link.source_name)
            sink = (link.sink_id, link.sink_name)
            prefix = f"Link {source} <-> {sink}"

            for i, (node_id, name) in enumerate([source, sink]):
                node = node_map.get(node_id)
                if not node:
                    raise ValueError(
                        f"{prefix}, {node_id} is invalid node id, available nodes: {node_map.keys()}"
                    )

                block = get_block(node.block_id)
                if not block:
                    blocks = {v().id: v().name for v in get_blocks().values()}
                    raise ValueError(
                        f"{prefix}, {node.block_id} is invalid block id, available blocks: {blocks}"
                    )

                sanitized_name = sanitize_pin_name(name)
                vals = node.input_default
                if i == 0:
                    fields = (
                        block.output_schema.get_fields()
                        if block.block_type not in [BlockType.AGENT]
                        else vals.get("output_schema", {}).get("properties", {}).keys()
                    )
                else:
                    fields = (
                        block.input_schema.get_fields()
                        if block.block_type not in [BlockType.AGENT]
                        else vals.get("input_schema", {}).get("properties", {}).keys()
                    )
                if sanitized_name not in fields and not is_tool_pin(name):
                    fields_msg = f"Allowed fields: {fields}"
                    raise ValueError(f"{prefix}, `{name}` invalid, {fields_msg}")

            if is_static_output_block(link.source_id):
                link.is_static = True