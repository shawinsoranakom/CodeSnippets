def _get_raw_content(vertex_output_data: Any) -> Any:
    """Extract raw content from vertex output data.

    Tries multiple fields in order: outputs, results, messages.
    Note: Uses 'is not None' checks to avoid treating empty collections as missing.

    Args:
        vertex_output_data: The output data from RunResponse

    Returns:
        Raw content or None
    """
    if hasattr(vertex_output_data, "outputs") and vertex_output_data.outputs is not None:
        return vertex_output_data.outputs
    if hasattr(vertex_output_data, "results") and vertex_output_data.results is not None:
        return vertex_output_data.results
    if hasattr(vertex_output_data, "messages") and vertex_output_data.messages is not None:
        return vertex_output_data.messages
    if isinstance(vertex_output_data, dict):
        # Check for 'results' first, then 'content' if results is None
        if "results" in vertex_output_data:
            return vertex_output_data["results"]
        if "content" in vertex_output_data:
            return vertex_output_data["content"]
    return vertex_output_data