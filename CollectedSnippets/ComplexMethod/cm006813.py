def extract_loop_output(results: list, end_vertex_id: str | None) -> Data:
    """Extract the output from subgraph execution results.

    Args:
        results: List of VertexBuildResult objects from subgraph execution
        end_vertex_id: The vertex ID that feeds back to the item input (end of loop body)

    Returns:
        Data object containing the loop iteration output
    """
    if not results:
        return Data(text="")

    if not end_vertex_id:
        return Data(text="")

    # Find the result for the end vertex
    for result in results:
        if hasattr(result, "vertex") and result.vertex.id == end_vertex_id and hasattr(result, "result_dict"):
            result_dict = result.result_dict
            if result_dict.outputs:
                # Get first output value
                first_output = next(iter(result_dict.outputs.values()))
                # Handle both dict (from model_dump()) and object formats
                message = None
                if isinstance(first_output, dict) and "message" in first_output:
                    message = first_output["message"]
                elif hasattr(first_output, "message"):
                    message = first_output.message

                if message is not None:
                    # If message is a dict, wrap it in a Data object
                    if isinstance(message, dict):
                        return Data(data=message)
                    # If it's already a Data object, return it directly
                    if isinstance(message, Data):
                        return message
                    # For other types, wrap in Data with text
                    return Data(text=str(message))

    return Data(text="")