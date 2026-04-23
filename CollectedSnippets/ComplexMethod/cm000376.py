async def _validate_node_input_credentials(
    graph: GraphModel,
    user_id: str,
    nodes_input_masks: Optional[NodesInputMasks] = None,
) -> tuple[dict[str, dict[str, str]], set[str]]:
    """
    Checks all credentials for all nodes of the graph and returns structured errors
    and a set of nodes that should be skipped due to optional missing credentials.

    Returns:
        tuple[
            dict[node_id, dict[field_name, error_message]]: Credential validation errors per node,
            set[node_id]: Nodes that should be skipped (optional credentials not configured)
        ]
    """
    credential_errors: dict[str, dict[str, str]] = defaultdict(dict)
    nodes_to_skip: set[str] = set()

    for node in graph.nodes:
        block = node.block

        # Find any fields of type CredentialsMetaInput
        credentials_fields = block.input_schema.get_credentials_fields()
        if not credentials_fields:
            continue

        # Track if any credential field is missing for this node
        has_missing_credentials = False

        # A credential field is optional if the node metadata says so, or if
        # the block schema declares a default for the field.
        required_fields = block.input_schema.get_required_fields()
        is_creds_optional = node.credentials_optional

        for field_name, credentials_meta_type in credentials_fields.items():
            field_is_optional = is_creds_optional or field_name not in required_fields
            try:
                # Check nodes_input_masks first, then input_default
                field_value = None
                if (
                    nodes_input_masks
                    and (node_input_mask := nodes_input_masks.get(node.id))
                    and field_name in node_input_mask
                ):
                    field_value = node_input_mask[field_name]
                elif field_name in node.input_default:
                    # For optional credentials, don't use input_default - treat as missing
                    # This prevents stale credential IDs from failing validation
                    if field_is_optional:
                        field_value = None
                    else:
                        field_value = node.input_default[field_name]

                # Check if credentials are missing (None, empty, or not present)
                if field_value is None or (
                    isinstance(field_value, dict) and not field_value.get("id")
                ):
                    has_missing_credentials = True
                    # If credential field is optional, skip instead of error
                    if field_is_optional:
                        continue  # Don't add error, will be marked for skip after loop
                    else:
                        credential_errors[node.id][field_name] = CRED_ERR_REQUIRED
                        continue

                credentials_meta = credentials_meta_type.model_validate(field_value)

            except ValidationError as e:
                # Validation error means credentials were provided but invalid
                # This should always be an error, even if optional
                credential_errors[node.id][
                    field_name
                ] = f"{CRED_ERR_INVALID_PREFIX} {e}"
                continue

            try:
                # Fetch the corresponding Credentials and perform sanity checks
                credentials = await get_integration_credentials_store().get_creds_by_id(
                    user_id, credentials_meta.id
                )
            except Exception as e:
                # Handle any errors fetching credentials
                # If credentials were explicitly configured but unavailable, it's an error
                credential_errors[node.id][
                    field_name
                ] = f"{CRED_ERR_NOT_AVAILABLE_PREFIX} {e}"
                continue

            if not credentials:
                credential_errors[node.id][
                    field_name
                ] = f"{CRED_ERR_UNKNOWN_PREFIX}{credentials_meta.id}"
                continue

            if (
                credentials.provider != credentials_meta.provider
                or credentials.type != credentials_meta.type
            ):
                logger.warning(
                    f"Invalid credentials #{credentials.id} for node #{node.id}: "
                    "type/provider mismatch: "
                    f"{credentials_meta.type}<>{credentials.type};"
                    f"{credentials_meta.provider}<>{credentials.provider}"
                )
                credential_errors[node.id][field_name] = CRED_ERR_INVALID_TYPE_MISMATCH
                continue

        # If node has optional credentials and any are missing, allow running without.
        # The executor will pass credentials=None to the block's run().
        if (
            has_missing_credentials
            and is_creds_optional
            and node.id not in credential_errors
        ):
            logger.info(
                f"Node #{node.id}: optional credentials not configured, "
                "running without"
            )

    return credential_errors, nodes_to_skip