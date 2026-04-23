async def prepare_block_for_execution(
    block_id: str,
    input_data: dict[str, Any],
    user_id: str,
    session: ChatSession,
    session_id: str,
    dry_run: bool,
) -> "BlockPreparation | ToolResponseBase":
    """Validate and prepare a block for execution.

    Performs: block lookup, disabled/excluded-type checks, credential resolution,
    input schema generation, file-ref expansion, missing-credentials check, and
    unrecognized-field validation.

    Does NOT check for missing required fields (tools differ: run_block shows a
    schema preview) and does NOT run the HITL review check (use check_hitl_review
    separately).

    Args:
        block_id: Block UUID to prepare.
        input_data: Input values provided by the caller.
        user_id: Authenticated user ID.
        session: Current chat session (needed for file-ref expansion).
        session_id: Chat session ID (used in error responses).

    Returns:
        BlockPreparation on success, or a ToolResponseBase error/setup response.
    """
    # Lazy import: find_block imports from .base and .models (siblings), not
    # from helpers — no actual circular dependency exists today.  Kept lazy as a
    # precaution since find_block is the block-registry module and future changes
    # could introduce a cycle.
    from .find_block import COPILOT_EXCLUDED_BLOCK_IDS, COPILOT_EXCLUDED_BLOCK_TYPES

    block = get_block(block_id)
    if not block:
        return ErrorResponse(
            message=f"Block '{block_id}' not found", session_id=session_id
        )
    if block.disabled:
        return ErrorResponse(
            message=f"Block '{block_id}' is disabled", session_id=session_id
        )

    if (
        block.block_type in COPILOT_EXCLUDED_BLOCK_TYPES
        or block.id in COPILOT_EXCLUDED_BLOCK_IDS
    ):
        if block.block_type == BlockType.MCP_TOOL:
            hint = (
                " Use the `run_mcp_tool` tool instead — it handles "
                "MCP server discovery, authentication, and execution."
            )
        elif block.block_type == BlockType.AGENT:
            hint = " Use the `run_agent` tool instead."
        else:
            hint = " This block is designed for use within graphs only."
        return ErrorResponse(
            message=f"Block '{block.name}' cannot be run directly.{hint}",
            session_id=session_id,
        )

    matched_credentials, missing_credentials = await resolve_block_credentials(
        user_id, block, input_data
    )

    try:
        input_schema: dict[str, Any] = block.input_schema.jsonschema()
    except Exception as e:
        logger.warning("Failed to generate input schema for block %s: %s", block_id, e)
        return ErrorResponse(
            message=f"Block '{block.name}' has an invalid input schema",
            error=str(e),
            session_id=session_id,
        )

    # Expand @@agptfile: refs using the block's input schema so string/list
    # fields get the correct deserialization.
    if input_data:
        try:
            input_data = await expand_file_refs_in_args(
                input_data, user_id, session, input_schema=input_schema
            )
        except FileRefExpansionError as exc:
            return ErrorResponse(
                message=(
                    f"Failed to resolve file reference: {exc}. "
                    "Ensure the file exists before referencing it."
                ),
                session_id=session_id,
            )

    credentials_fields = set(block.input_schema.get_credentials_fields().keys())

    if missing_credentials and not dry_run:
        credentials_fields_info = _resolve_discriminated_credentials(block, input_data)
        missing_creds_dict = build_missing_credentials_from_field_info(
            credentials_fields_info, set(matched_credentials.keys())
        )
        missing_creds_list = list(missing_creds_dict.values())
        return SetupRequirementsResponse(
            message=(
                f"Block '{block.name}' requires credentials that are not configured. "
                "Please set up the required credentials before running this block."
            ),
            session_id=session_id,
            setup_info=SetupInfo(
                agent_id=block_id,
                agent_name=block.name,
                user_readiness=UserReadiness(
                    has_all_credentials=False,
                    missing_credentials=missing_creds_dict,
                    ready_to_run=False,
                ),
                requirements={
                    "credentials": missing_creds_list,
                    "inputs": get_inputs_from_schema(
                        input_schema,
                        exclude_fields=credentials_fields,
                        input_data=input_data,
                    ),
                    "execution_modes": ["immediate"],
                },
            ),
            graph_id=None,
            graph_version=None,
        )
    required_keys = set(input_schema.get("required", []))
    required_non_credential_keys = required_keys - credentials_fields
    provided_input_keys = set(input_data.keys()) - credentials_fields

    valid_fields = set(input_schema.get("properties", {}).keys()) - credentials_fields
    unrecognized_fields = provided_input_keys - valid_fields
    if unrecognized_fields:
        return InputValidationErrorResponse(
            message=(
                f"Unknown input field(s) provided: {', '.join(sorted(unrecognized_fields))}. "
                "Block was not executed. Please use the correct field names from the schema."
            ),
            session_id=session_id,
            unrecognized_fields=sorted(unrecognized_fields),
            inputs=input_schema,
        )

    synthetic_graph_id = f"{COPILOT_SESSION_PREFIX}{session_id}"
    synthetic_node_id = f"{COPILOT_NODE_PREFIX}{block_id}"

    return BlockPreparation(
        block=block,
        block_id=block_id,
        input_data=input_data,
        matched_credentials=matched_credentials,
        input_schema=input_schema,
        credentials_fields=credentials_fields,
        required_non_credential_keys=required_non_credential_keys,
        provided_input_keys=provided_input_keys,
        synthetic_graph_id=synthetic_graph_id,
        synthetic_node_id=synthetic_node_id,
    )