def get_chat_output_sender_name(self) -> str | None:
    """Get sender_name from ChatOutput component."""
    if not hasattr(self, "graph") or not self.graph:
        return None

    # Check if graph has vertices attribute (PlaceholderGraph doesn't)
    if not hasattr(self.graph, "vertices"):
        return None

    for vertex in self.graph.vertices:
        # Safely check if vertex has data attribute, correct type, and raw_params
        if (
            hasattr(vertex, "data")
            and vertex.data.get("type") == "ChatOutput"
            and hasattr(vertex, "raw_params")
            and vertex.raw_params
        ):
            return vertex.raw_params.get("sender_name")

    return None