def validate_exec(
    node: Node,
    data: BlockInput,
    resolve_input: bool = True,
    dry_run: bool = False,
) -> tuple[BlockInput | None, str]:
    """
    Validate the input data for a node execution.

    Args:
        node: The node to execute.
        data: The input data for the node execution.
        resolve_input: Whether to resolve dynamic pins into dict/list/object.
        dry_run: When True, credential fields are allowed to be missing — they
            will be substituted with a sentinel so the node can be queued and
            later executed via simulate_block.

    Returns:
        A tuple of the validated data and the block name.
        If the data is invalid, the first element will be None, and the second element
        will be an error message.
        If the data is valid, the first element will be the resolved input data, and
        the second element will be the block name.
    """
    node_block = get_block(node.block_id)
    if not node_block:
        return None, f"Block for {node.block_id} not found."
    schema = node_block.input_schema

    # Input data (without default values) should contain all required fields.
    error_prefix = f"Input data missing or mismatch for `{node_block.name}`:"
    if missing_links := schema.get_missing_links(data, node.input_links):
        return None, f"{error_prefix} unpopulated links {missing_links}"

    # For dry runs, supply sentinel values for any missing credential fields so
    # the node can be queued — simulate_block never calls the real API anyway.
    if dry_run:
        cred_field_names = set(schema.get_credentials_fields().keys())
        for field_name in cred_field_names:
            if field_name not in data:
                data = {**data, field_name: None}

    # Merge input data with default values and resolve dynamic dict/list/object pins.
    input_default = schema.get_input_defaults(node.input_default)
    data = {**input_default, **data}
    if resolve_input:
        data = merge_execution_input(data)

    # Coerce non-matching data types to the expected input schema.
    coerce_inputs_to_schema(data, schema)

    # Input data post-merge should contain all required fields from the schema.
    if missing_input := schema.get_missing_input(data):
        if dry_run:
            # In dry-run mode all missing inputs are tolerated — simulate_block()
            # generates synthetic outputs without needing real input values.
            pass
        else:
            return None, f"{error_prefix} missing input {missing_input}"

    # Last validation: Validate the input values against the schema.
    # Skip for dry runs — simulate_block doesn't use real inputs, and sentinel
    # credential values (None) would fail JSON-schema type/required checks.
    if not dry_run:
        if error := schema.get_mismatch_error(data):
            error_message = f"{error_prefix} {error}"
            logger.warning(error_message)
            return None, error_message

    return data, node_block.name