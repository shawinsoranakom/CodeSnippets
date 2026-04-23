def _process_terminal_vertex(
    vertex: Any,
    output_data_map: dict[str, Any],
) -> tuple[str, ComponentOutput]:
    """Process a single terminal vertex and return (output_key, component_output).

    Args:
        vertex: The vertex to process
        output_data_map: Map of component_id to output data

    Returns:
        Tuple of (output_key, ComponentOutput)
    """
    # Get output data by vertex.id (component_id)
    vertex_output_data = output_data_map.get(vertex.id)

    # Determine output type from vertex
    output_type = "unknown"
    if vertex.outputs and len(vertex.outputs) > 0:
        types = vertex.outputs[0].get("types", [])
        if types:
            output_type = types[0].lower()
    if output_type == "unknown" and vertex.vertex_type:
        output_type = vertex.vertex_type.lower()

    # Initialize metadata with component_type
    metadata: dict[str, Any] = {"component_type": vertex.vertex_type}

    # Extract content
    content = None
    if vertex_output_data:
        raw_content = _get_raw_content(vertex_output_data)

        if vertex.is_output and raw_content is not None:
            # Output nodes: simplify content
            content = _simplify_output_content(raw_content, output_type)
        elif not vertex.is_output and raw_content is not None:
            # Non-output nodes:
            # - For data types: extract and show content
            # - For message types: extract metadata only (source, file_path)
            # TODO: Future scope - Add support for "dataframe" output type
            if output_type in ["data", "dataframe"]:
                # Show data content for non-output data nodes
                content = _simplify_output_content(raw_content, output_type)
            else:
                # For message types, extract metadata only
                extra_metadata = _build_metadata_for_non_output(
                    raw_content,
                    vertex.id,
                    vertex.display_name or vertex.vertex_type,
                    vertex.vertex_type,
                    output_type,
                )
                metadata.update(extra_metadata)

        # Add any additional metadata from result data
        if hasattr(vertex_output_data, "metadata") and vertex_output_data.metadata:
            metadata.update(vertex_output_data.metadata)
        elif isinstance(vertex_output_data, dict) and "metadata" in vertex_output_data:
            result_metadata = vertex_output_data.get("metadata")
            if isinstance(result_metadata, dict):
                metadata.update(result_metadata)

    # Determine output key: use vertex id but TODO: add alias handling when avialable
    output_key = vertex.id

    # Build ComponentOutput
    component_output = ComponentOutput(
        type=output_type,
        component_id=vertex.id,
        status=JobStatus.COMPLETED,
        content=content,
        metadata=metadata,
    )
    return output_key, component_output