def update_edges_with_latest_component_versions(project_data):
    """Update edges in a project with the latest component versions.

    This function processes each edge in the project data and ensures that the source and target handles
    are updated to match the latest component versions. It tracks all changes made to edges in a log
    for debugging purposes.

    Args:
        project_data (dict): The project data containing nodes and edges to be updated.

    Returns:
        dict: A deep copy of the project data with updated edges.

    The function performs the following operations:
    1. Creates a deep copy of the project data to avoid modifying the original
    2. For each edge, extracts and parses the source and target handles
    3. Finds the corresponding source and target nodes
    4. Updates output types in the source handle based on the node's outputs
    5. Updates input types in the target handle based on the node's template
    6. Escapes and updates the handles in the edge data
    7. Logs all changes made to the edges
    """
    # Initialize a dictionary to track changes for logging
    edge_changes_log = defaultdict(list)
    # Create a deep copy to avoid modifying the original data
    project_data_copy = deepcopy(project_data)

    # Create a mapping of node types to node IDs for node reconciliation
    node_type_map = {}
    for node in project_data_copy.get("nodes", []):
        node_type = node.get("data", {}).get("type", "")
        if node_type:
            if node_type not in node_type_map:
                node_type_map[node_type] = []
            node_type_map[node_type].append(node.get("id"))

    # Process each edge in the project
    for edge in project_data_copy.get("edges", []):
        # Extract and parse source and target handles
        source_handle = edge.get("data", {}).get("sourceHandle")
        source_handle = scape_json_parse(source_handle)
        target_handle = edge.get("data", {}).get("targetHandle")
        target_handle = scape_json_parse(target_handle)

        # Find the corresponding source and target nodes
        source_node = next(
            (node for node in project_data_copy.get("nodes", []) if node.get("id") == edge.get("source")),
            None,
        )
        target_node = next(
            (node for node in project_data_copy.get("nodes", []) if node.get("id") == edge.get("target")),
            None,
        )

        # Try to reconcile missing nodes by type
        if source_node is None and source_handle and "dataType" in source_handle:
            node_type = source_handle.get("dataType")
            if node_type_map.get(node_type):
                # Use the first node of matching type as replacement
                new_node_id = node_type_map[node_type][0]
                logger.info(f"Reconciling missing source node: replacing {edge.get('source')} with {new_node_id}")

                # Update edge source
                edge["source"] = new_node_id

                # Update source handle ID
                source_handle["id"] = new_node_id

                # Find the new source node
                source_node = next(
                    (node for node in project_data_copy.get("nodes", []) if node.get("id") == new_node_id),
                    None,
                )

                # Update edge ID (complex as it contains encoded handles)
                # This is a simplified approach - in production you'd need to parse and rebuild the ID
                old_id_prefix = edge.get("id", "").split("{")[0]
                if old_id_prefix:
                    new_id_prefix = old_id_prefix.replace(edge.get("source"), new_node_id)
                    edge["id"] = edge.get("id", "").replace(old_id_prefix, new_id_prefix)

        if target_node is None and target_handle and "id" in target_handle:
            # Extract node type from target handle ID (e.g., "AstraDBGraph-jr8pY" -> "AstraDBGraph")
            id_parts = target_handle.get("id", "").split("-")
            if len(id_parts) > 0:
                node_type = id_parts[0]
                if node_type_map.get(node_type):
                    # Use the first node of matching type as replacement
                    new_node_id = node_type_map[node_type][0]
                    logger.info(f"Reconciling missing target node: replacing {edge.get('target')} with {new_node_id}")

                    # Update edge target
                    edge["target"] = new_node_id

                    # Update target handle ID
                    target_handle["id"] = new_node_id

                    # Find the new target node
                    target_node = next(
                        (node for node in project_data_copy.get("nodes", []) if node.get("id") == new_node_id),
                        None,
                    )

                    # Update edge ID (simplified approach)
                    old_id_suffix = edge.get("id", "").split("}-")[1] if "}-" in edge.get("id", "") else ""
                    if old_id_suffix:
                        new_id_suffix = old_id_suffix.replace(edge.get("target"), new_node_id)
                        edge["id"] = edge.get("id", "").replace(old_id_suffix, new_id_suffix)

        if source_node and target_node:
            # Extract node data for easier access
            source_node_data = source_node.get("data", {}).get("node", {})
            target_node_data = target_node.get("data", {}).get("node", {})

            # Find the output data that matches the source handle name
            output_data = next(
                (
                    output
                    for output in source_node_data.get("outputs", [])
                    if output.get("name") == source_handle.get("name")
                ),
                None,
            )

            # If not found by name, try to find by display_name
            if not output_data:
                output_data = next(
                    (
                        output
                        for output in source_node_data.get("outputs", [])
                        if output.get("display_name") == source_handle.get("name")
                    ),
                    None,
                )
                # Update source handle name if found by display_name
                if output_data:
                    source_handle["name"] = output_data.get("name")

            # Determine the new output types based on the output data
            # Always prefer "types" over "selected" to ensure we use the current type names (JSON/Table)
            # rather than potentially stale "selected" values (Data/DataFrame)
            if output_data:
                if len(output_data.get("types", [])) == 1:
                    new_output_types = output_data.get("types", [])
                elif len(output_data.get("types", [])) > 1 and output_data.get("selected"):
                    # Only use "selected" if there are multiple types available
                    # and selected is present
                    selected = output_data.get("selected")
                    # Migrate old type names to new ones
                    type_migrations = {
                        "Data": "JSON",
                        "DataFrame": "Table",
                    }
                    migrated_selected = type_migrations.get(selected, selected)
                    # Verify the migrated selected is in the available types
                    if migrated_selected in output_data.get("types", []):
                        new_output_types = [migrated_selected]
                    else:
                        # Fallback to first type if selected is invalid
                        new_output_types = output_data.get("types", [])
                else:
                    new_output_types = output_data.get("types", [])
            else:
                new_output_types = []

            # Update output types if they've changed and log the change
            if source_handle.get("output_types", []) != new_output_types:
                edge_changes_log[source_node_data.get("display_name", "unknown")].append(
                    {
                        "attr": "output_types",
                        "old_value": source_handle.get("output_types", []),
                        "new_value": new_output_types,
                    }
                )
                source_handle["output_types"] = new_output_types

            # Update input types if they've changed and log the change
            field_name = target_handle.get("fieldName")
            if field_name in target_node_data.get("template", {}) and target_handle.get(
                "inputTypes", []
            ) != target_node_data.get("template", {}).get(field_name, {}).get("input_types", []):
                edge_changes_log[target_node_data.get("display_name", "unknown")].append(
                    {
                        "attr": "inputTypes",
                        "old_value": target_handle.get("inputTypes", []),
                        "new_value": target_node_data.get("template", {}).get(field_name, {}).get("input_types", []),
                    }
                )
                target_handle["inputTypes"] = (
                    target_node_data.get("template", {}).get(field_name, {}).get("input_types", [])
                )

            # Escape the updated handles for JSON storage
            escaped_source_handle = escape_json_dump(source_handle)
            escaped_target_handle = escape_json_dump(target_handle)

            # Try to parse and escape the old handles for comparison
            try:
                old_escape_source_handle = escape_json_dump(json.loads(edge.get("sourceHandle", "{}")))
            except (json.JSONDecodeError, TypeError):
                old_escape_source_handle = edge.get("sourceHandle", "")

            try:
                old_escape_target_handle = escape_json_dump(json.loads(edge.get("targetHandle", "{}")))
            except (json.JSONDecodeError, TypeError):
                old_escape_target_handle = edge.get("targetHandle", "")

            # Update source handle if it's changed and log the change
            if old_escape_source_handle != escaped_source_handle:
                edge_changes_log[source_node_data.get("display_name", "unknown")].append(
                    {
                        "attr": "sourceHandle",
                        "old_value": old_escape_source_handle,
                        "new_value": escaped_source_handle,
                    }
                )
                edge["sourceHandle"] = escaped_source_handle
                if "data" in edge:
                    edge["data"]["sourceHandle"] = source_handle

            # Update target handle if it's changed and log the change
            if old_escape_target_handle != escaped_target_handle:
                edge_changes_log[target_node_data.get("display_name", "unknown")].append(
                    {
                        "attr": "targetHandle",
                        "old_value": old_escape_target_handle,
                        "new_value": escaped_target_handle,
                    }
                )
                edge["targetHandle"] = escaped_target_handle
                if "data" in edge:
                    edge["data"]["targetHandle"] = target_handle

        else:
            # Log an error if source or target node is not found after reconciliation attempt
            logger.error(f"Source or target node not found for edge: {edge}")

    # Log all the changes that were made
    log_node_changes(edge_changes_log)
    return project_data_copy