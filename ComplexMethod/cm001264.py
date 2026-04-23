async def _fetch_graph_data(
        request: ChatRequest, user_id: str
    ) -> Optional[GraphData]:
        """Fetch graph data if requested and available."""
        if not (request.include_graph_data and request.graph_id):
            return None

        try:
            graph = await graph_db.get_graph(
                graph_id=request.graph_id, version=None, user_id=user_id
            )
            if not graph:
                return None

            nodes_data = []
            for node in graph.nodes:
                block = get_block(node.block_id)
                if not block:
                    continue

                node_data = {
                    "id": node.id,
                    "block_id": node.block_id,
                    "block_name": block.name,
                    "block_type": (
                        block.block_type.value if hasattr(block, "block_type") else None
                    ),
                    "data": {
                        k: v
                        for k, v in (node.input_default or {}).items()
                        if k not in ["credentials"]  # Exclude sensitive data
                    },
                }
                nodes_data.append(node_data)

            # Create a GraphData object with the required fields
            return GraphData(
                nodes=nodes_data,
                edges=[],
                graph_name=graph.name,
                graph_description=graph.description,
            )
        except Exception as e:
            logger.error(f"Failed to fetch graph data: {str(e)}")
            return None