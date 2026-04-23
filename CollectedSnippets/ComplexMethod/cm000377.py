async def _construct_starting_node_execution_input(
    graph: GraphModel,
    user_id: str,
    graph_inputs: GraphInput,
    nodes_input_masks: Optional[NodesInputMasks] = None,
    dry_run: bool = False,
) -> tuple[list[tuple[str, BlockInput]], set[str]]:
    """
    Validates and prepares the input data for executing a graph.
    This function checks the graph for starting nodes, validates the input data
    against the schema, and resolves dynamic input pins into a single list,
    dictionary, or object.

    Args:
        graph (GraphModel): The graph model to execute.
        user_id (str): The ID of the user executing the graph.
        data (GraphInput): The input data for the graph execution.
        node_credentials_map: `dict[node_id, dict[input_name, CredentialsMetaInput]]`
        dry_run: When True, skip credential validation errors (simulation needs no real creds).

    Returns:
        tuple[
            list[tuple[str, BlockInput]]: A list of tuples, each containing the node ID
                and the corresponding input data for that node.
            set[str]: Node IDs that should be skipped (optional credentials not configured)
        ]
    """
    # Use new validation function that includes credentials
    validation_errors, nodes_to_skip = await validate_graph_with_credentials(
        graph, user_id, nodes_input_masks
    )
    # Dry runs simulate every block — missing credentials are irrelevant.
    # Strip credential-only errors so the graph can proceed.
    if dry_run and validation_errors:
        validation_errors = {
            node_id: {
                field: msg
                for field, msg in errors.items()
                if not is_credential_validation_error_message(msg)
            }
            for node_id, errors in validation_errors.items()
        }
        # Remove nodes that have no remaining errors
        validation_errors = {
            node_id: errors for node_id, errors in validation_errors.items() if errors
        }
    n_error_nodes = len(validation_errors)
    n_errors = sum(len(errors) for errors in validation_errors.values())
    if validation_errors:
        raise GraphValidationError(
            f"Graph validation failed: {n_errors} issues on {n_error_nodes} nodes",
            node_errors=validation_errors,
        )

    nodes_input = []
    for node in graph.starting_nodes:
        input_data = {}
        block = node.block

        # Note block should never be executed.
        if block.block_type == BlockType.NOTE:
            continue

        # Extract request input data, and assign it to the input pin.
        if block.block_type == BlockType.INPUT:
            input_name = cast(str | None, node.input_default.get("name"))
            if input_name and input_name in graph_inputs:
                input_data = {"value": graph_inputs[input_name]}

        # Apply node input overrides
        if nodes_input_masks and (node_input_mask := nodes_input_masks.get(node.id)):
            input_data.update(node_input_mask)

        # Webhook-triggered agents cannot be executed directly without payload data.
        # Legitimate webhook triggers provide payload via nodes_input_masks above.
        if (
            block.block_type
            in (
                BlockType.WEBHOOK,
                BlockType.WEBHOOK_MANUAL,
            )
            and "payload" not in input_data
        ):
            raise ValueError(
                "This agent is triggered by an external event (webhook) "
                "and cannot be executed directly. "
                "Please use the appropriate trigger to run this agent."
            )

        input_data, error = validate_exec(node, input_data, dry_run=dry_run)
        if input_data is None:
            raise ValueError(error)
        else:
            nodes_input.append((node.id, input_data))

    if not nodes_input:
        raise ValueError(
            "No starting nodes found for the graph, make sure an AgentInput or blocks with no inbound links are present as starting nodes."
        )

    return nodes_input, nodes_to_skip