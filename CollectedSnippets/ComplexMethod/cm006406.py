async def get_flow_graph_representations(
    flow_id_or_name: str,
    user_id: str | UUID | None = None,
) -> dict[str, Any]:
    """Get both ASCII and text representations of a flow graph.

    Args:
        flow_id_or_name: Flow ID (UUID) or endpoint name.
        user_id: Optional user ID to filter flows.

    Returns:
        Dictionary containing:
        - flow_id: The flow ID
        - flow_name: The flow name
        - ascii_graph: ASCII art representation of the graph
        - text_repr: Text representation with vertices and edges
        - vertex_count: Number of vertices in the graph
        - edge_count: Number of edges in the graph
        - error: Error message if any (only if operation fails)

    Example:
        >>> result = await get_flow_graph_representations("my-flow-id")
        >>> print(result["ascii_graph"])
        >>> print(result["text_repr"])
    """
    try:
        # Get the flow
        flow: FlowRead | None = await get_flow_by_id_or_endpoint_name(flow_id_or_name, user_id)

        if flow is None:
            return {
                "error": f"Flow {flow_id_or_name} not found",
                "flow_id": flow_id_or_name,
            }

        if flow.data is None:
            return {
                "error": f"Flow {flow_id_or_name} has no data",
                "flow_id": str(flow.id),
                "flow_name": flow.name,
            }

        # Create graph from flow data
        flow_id_str = str(flow.id)
        graph = Graph.from_payload(
            flow.data,
            flow_id=flow_id_str,
            flow_name=flow.name,
        )

        # Get text representation using __repr__
        text_repr = repr(graph)

        # Get ASCII representation using draw_graph
        # Extract vertex and edge data for ASCII drawing
        vertices = [vertex.id for vertex in graph.vertices]
        edges = [(edge.source_id, edge.target_id) for edge in graph.edges]

        ascii_graph = None
        if vertices and edges:
            try:
                ascii_graph = draw_graph(vertices, edges, return_ascii=True)
            except Exception as e:  # noqa: BLE001
                await logger.awarning(f"Failed to generate ASCII graph: {e}")
                ascii_graph = "ASCII graph generation failed (graph may be too complex or have cycles)"

        return {
            "flow_id": flow_id_str,
            "flow_name": flow.name,
            "ascii_graph": ascii_graph,
            "text_repr": text_repr,
            "vertex_count": len(graph.vertices),
            "edge_count": len(graph.edges),
            "tags": flow.tags,
            "description": flow.description,
        }

    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error getting flow graph representations for {flow_id_or_name}: {e}")
        return {
            "error": str(e),
            "flow_id": flow_id_or_name,
        }

    finally:
        await logger.ainfo("Getting flow graph representations completed")