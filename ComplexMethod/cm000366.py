async def execute_node(
    node: Node,
    data: NodeExecutionEntry,
    execution_processor: "ExecutionProcessor",
    execution_stats: NodeExecutionStats | None = None,
    nodes_input_masks: Optional[NodesInputMasks] = None,
    nodes_to_skip: Optional[set[str]] = None,
) -> BlockOutput:
    """
    Execute a node in the graph. This will trigger a block execution on a node,
    persist the execution result, and return the subsequent node to be executed.

    Args:
        db_client: The client to send execution updates to the server.
        creds_manager: The manager to acquire and release credentials.
        data: The execution data for executing the current node.
        execution_stats: The execution statistics to be updated.

    Returns:
        The subsequent node to be enqueued, or None if there is no subsequent node.
    """
    user_id = data.user_id
    graph_exec_id = data.graph_exec_id
    graph_id = data.graph_id
    graph_version = data.graph_version
    node_exec_id = data.node_exec_id
    node_id = data.node_id
    node_block = node.block
    execution_context = data.execution_context
    creds_manager = execution_processor.creds_manager

    log_metadata = LogMetadata(
        logger=_logger,
        user_id=user_id,
        graph_eid=graph_exec_id,
        graph_id=graph_id,
        node_eid=node_exec_id,
        node_id=node_id,
        block_name=node_block.name,
    )

    if node_block.disabled:
        raise ValueError(f"Block {node_block.id} is disabled and cannot be executed")

    # Sanity check: validate the execution input.
    input_data, error = validate_exec(
        node, data.inputs, resolve_input=False, dry_run=execution_context.dry_run
    )
    if input_data is None:
        log_metadata.warning(f"Skip execution, input validation error: {error}")
        yield "error", error
        return

    # Re-shape the input data for agent block.
    # AgentExecutorBlock specially separate the node input_data & its input_default.
    if isinstance(node_block, AgentExecutorBlock):
        _input_data = AgentExecutorBlock.Input(**node.input_default)
        _input_data.inputs = input_data
        if nodes_input_masks:
            _input_data.nodes_input_masks = nodes_input_masks
        _input_data.user_id = user_id
        input_data = _input_data.model_dump()
    elif isinstance(node_block, MCPToolBlock):
        _mcp_data = MCPToolBlock.Input(**node.input_default)
        # Dynamic tool fields are flattened to top-level by validate_exec
        # (via get_input_defaults). Collect them back into tool_arguments.
        tool_schema = _mcp_data.tool_input_schema
        tool_props = set(tool_schema.get("properties", {}).keys())
        merged_args = {**_mcp_data.tool_arguments}
        for key in tool_props:
            if key in input_data:
                merged_args[key] = input_data[key]
        _mcp_data.tool_arguments = merged_args
        input_data = _mcp_data.model_dump()
    data.inputs = input_data

    # Execute the node
    input_data_str = json.dumps(input_data)
    input_size = len(input_data_str)
    log_metadata.debug("Executed node with input", input=input_data_str)

    # Create node-specific execution context to avoid race conditions
    # (multiple nodes can execute concurrently and would otherwise mutate shared state)
    execution_context = execution_context.model_copy(
        update={"node_id": node_id, "node_exec_id": node_exec_id}
    )

    # Inject extra execution arguments for the blocks via kwargs
    # Keep individual kwargs for backwards compatibility with existing blocks
    extra_exec_kwargs: dict = {
        "graph_id": graph_id,
        "graph_version": graph_version,
        "node_id": node_id,
        "graph_exec_id": graph_exec_id,
        "node_exec_id": node_exec_id,
        "user_id": user_id,
        "execution_context": execution_context,
        "execution_processor": execution_processor,
        "nodes_to_skip": nodes_to_skip or set(),
    }

    # For special blocks in dry-run, prepare_dry_run returns a (possibly
    # modified) copy of input_data so the block executes for real.  For all
    # other blocks it returns None -> use LLM simulator.
    # OrchestratorBlock uses the platform's simulation model + OpenRouter key
    # so no user credentials are needed.
    _dry_run_input: dict[str, Any] | None = None
    if execution_context.dry_run:
        _dry_run_input = prepare_dry_run(node_block, input_data)
    if _dry_run_input is not None:
        input_data = _dry_run_input

    # Check for dry-run platform credentials (OrchestratorBlock uses the
    # platform's OpenRouter key instead of user credentials).
    _dry_run_creds = get_dry_run_credentials(input_data) if _dry_run_input else None

    # Last-minute fetch credentials + acquire a system-wide read-write lock to prevent
    # changes during execution. ⚠️ This means a set of credentials can only be used by
    # one (running) block at a time; simultaneous execution of blocks using same
    # credentials is not supported.
    creds_locks: list[AsyncRedisLock] = []
    input_model = cast(type[BlockSchema], node_block.input_schema)

    # Handle regular credentials fields
    for field_name, input_type in input_model.get_credentials_fields().items():
        # Dry-run platform credentials bypass the credential store.
        # Keep the existing credential metadata so _execute's input_schema(**...)
        # doesn't fail on the required field.  If no metadata is present,
        # synthesize a minimal placeholder from the platform credentials.
        if _dry_run_creds is not None:
            if input_data.get(field_name) is None:
                input_data[field_name] = {
                    "id": _dry_run_creds.id,
                    "provider": _dry_run_creds.provider,
                    "type": _dry_run_creds.type,
                    "title": _dry_run_creds.title,
                }
            extra_exec_kwargs[field_name] = _dry_run_creds
            continue

        field_value = input_data.get(field_name)
        if not field_value or (
            isinstance(field_value, dict) and not field_value.get("id")
        ):
            # No credentials configured — nullify so JSON schema validation
            # doesn't choke on the empty default `{}`.
            input_data[field_name] = None
            continue  # Block runs without credentials

        credentials_meta = input_type(**field_value)
        # Write normalized values back so JSON schema validation also passes
        # (model_validator may have fixed legacy formats like "ProviderName.MCP")
        input_data[field_name] = credentials_meta.model_dump(mode="json")
        try:
            credentials, lock = await creds_manager.acquire(
                user_id, credentials_meta.id
            )
        except ValueError:
            # Credential was deleted or doesn't exist.
            # If the field has a default, run without credentials.
            if input_model.model_fields[field_name].default is not None:
                log_metadata.warning(
                    f"Credentials #{credentials_meta.id} not found, "
                    "running without (field has default)"
                )
                input_data[field_name] = None
                continue
            raise
        creds_locks.append(lock)
        extra_exec_kwargs[field_name] = credentials

    # Handle auto-generated credentials (e.g., from GoogleDriveFileInput)
    for kwarg_name, info in input_model.get_auto_credentials_fields().items():
        field_name = info["field_name"]
        field_data = input_data.get(field_name)
        if field_data and isinstance(field_data, dict):
            # Check if _credentials_id key exists in the field data
            if "_credentials_id" in field_data:
                cred_id = field_data["_credentials_id"]
                if cred_id:
                    # Credential ID provided - acquire credentials
                    provider = info.get("config", {}).get(
                        "provider", "external service"
                    )
                    file_name = field_data.get("name", "selected file")
                    try:
                        credentials, lock = await creds_manager.acquire(
                            user_id, cred_id
                        )
                        creds_locks.append(lock)
                        extra_exec_kwargs[kwarg_name] = credentials
                    except ValueError:
                        # Credential was deleted or doesn't exist
                        raise ValueError(
                            f"Authentication expired for '{file_name}' in field '{field_name}'. "
                            f"The saved {provider.capitalize()} credentials no longer exist. "
                            f"Please re-select the file to re-authenticate."
                        )
                # else: _credentials_id is explicitly None, skip credentials (for chained data)
            else:
                # _credentials_id key missing entirely - this is an error
                provider = info.get("config", {}).get("provider", "external service")
                file_name = field_data.get("name", "selected file")
                raise ValueError(
                    f"Authentication missing for '{file_name}' in field '{field_name}'. "
                    f"Please re-select the file to authenticate with {provider.capitalize()}."
                )

    output_size = 0

    # sentry tracking nonsense to get user counts for blocks because isolation scopes don't work :(
    scope = _sentry_get_current_scope()

    # save the tags
    original_user = scope._user
    original_tags = dict(scope._tags) if scope._tags else {}
    # Set user ID for error tracking
    scope.set_user({"id": user_id})

    scope.set_tag("graph_id", graph_id)
    scope.set_tag("node_id", node_id)
    scope.set_tag("block_name", node_block.name)
    scope.set_tag("block_id", node_block.id)
    for k, v in execution_context.model_dump().items():
        scope.set_tag(f"execution_context.{k}", v)

    try:
        if execution_context.dry_run and _dry_run_input is None:
            block_iter = simulate_block(node_block, input_data, user_id=user_id)
        else:
            block_iter = node_block.execute(input_data, **extra_exec_kwargs)

        async for output_name, output_data in block_iter:
            output_data = json.to_dict(output_data)
            output_size += len(json.dumps(output_data))
            log_metadata.debug("Node produced output", **{output_name: output_data})
            yield output_name, output_data
    except Exception as ex:
        # Only capture unexpected errors to Sentry, not user-caused ones.
        # Most ValueError subclasses here are expected (BlockExecutionError,
        # InsufficientBalanceError, plain ValueError for auth/disabled blocks, etc.)
        # but NotFoundError/GraphNotFoundError could indicate real platform issues.
        is_expected = isinstance(ex, ValueError) and not isinstance(
            ex, (NotFoundError, GraphNotFoundError)
        )
        if not is_expected:
            _sentry_capture_exception(error=ex, scope=scope)
            _sentry_flush()
        # Re-raise to maintain normal error flow
        raise
    finally:
        # Ensure all credentials are released even if execution fails
        for creds_lock in creds_locks:
            if (
                creds_lock
                and (await creds_lock.locked())
                and (await creds_lock.owned())
            ):
                try:
                    await creds_lock.release()
                except Exception as e:
                    log_metadata.error(f"Failed to release credentials lock: {e}")

        # Update execution stats
        if execution_stats is not None:
            execution_stats += node_block.execution_stats
            execution_stats.input_size = input_size
            execution_stats.output_size = output_size

        # Restore scope AFTER error has been captured
        scope._user = original_user
        scope._tags = original_tags