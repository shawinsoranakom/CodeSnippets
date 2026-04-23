async def execute_block(
    *,
    block: AnyBlockSchema,
    block_id: str,
    input_data: dict[str, Any],
    user_id: str,
    session_id: str,
    node_exec_id: str,
    matched_credentials: dict[str, CredentialsMetaInput],
    sensitive_action_safe_mode: bool = False,
    dry_run: bool,
) -> ToolResponseBase:
    """Execute a block with full context setup, credential injection, and error handling.

    This is the shared execution path used by both ``run_block`` (after review
    check) and ``continue_run_block`` (after approval).

    Returns:
        BlockOutputResponse on success, ErrorResponse on failure.
    """
    # Dry-run path: simulate the block with an LLM, no real execution.
    # HITL review is intentionally skipped — no real execution occurs.
    if dry_run:
        try:
            # Coerce types to match the block's input schema, same as real execution.
            # This ensures the simulated preview is consistent with real execution
            # (e.g., "42" → 42, string booleans → bool, enum defaults applied).
            coerce_inputs_to_schema(input_data, block.input_schema)
            outputs: dict[str, list[Any]] = defaultdict(list)
            async for output_name, output_data in simulate_block(
                block, input_data, user_id=user_id
            ):
                outputs[output_name].append(output_data)
            # simulator signals internal failure via ("error", "[SIMULATOR ERROR …]")
            sim_error = outputs.get("error", [])
            if (
                sim_error
                and isinstance(sim_error[0], str)
                and sim_error[0].startswith("[SIMULATOR ERROR")
            ):
                return ErrorResponse(
                    message=sim_error[0],
                    error=sim_error[0],
                    session_id=session_id,
                )

            return BlockOutputResponse(
                message=f"Block '{block.name}' executed successfully",
                block_id=block_id,
                block_name=block.name,
                outputs=dict(outputs),
                success=True,
                is_dry_run=True,
                session_id=session_id,
            )
        except Exception as e:
            logger.error("Dry-run simulation failed: %s", e, exc_info=True)
            return ErrorResponse(
                message=f"Dry-run simulation failed: {e}",
                error=str(e),
                session_id=session_id,
            )

    try:
        workspace = await workspace_db().get_or_create_workspace(user_id)

        synthetic_graph_id = f"{COPILOT_SESSION_PREFIX}{session_id}"
        synthetic_node_id = f"{COPILOT_NODE_PREFIX}{block_id}"

        execution_context = ExecutionContext(
            user_id=user_id,
            graph_id=synthetic_graph_id,
            graph_exec_id=synthetic_graph_id,
            graph_version=1,
            node_id=synthetic_node_id,
            node_exec_id=node_exec_id,
            workspace_id=workspace.id,
            session_id=session_id,
            sensitive_action_safe_mode=sensitive_action_safe_mode,
        )

        exec_kwargs: dict[str, Any] = {
            "user_id": user_id,
            "execution_context": execution_context,
            "workspace_id": workspace.id,
            "graph_exec_id": synthetic_graph_id,
            "node_exec_id": node_exec_id,
            "node_id": synthetic_node_id,
            "graph_version": 1,
            "graph_id": synthetic_graph_id,
        }

        # Inject credentials
        creds_manager = IntegrationCredentialsManager()
        for field_name, cred_meta in matched_credentials.items():
            if field_name not in input_data:
                input_data[field_name] = cred_meta.model_dump()

            actual_credentials = await creds_manager.get(
                user_id, cred_meta.id, lock=False
            )
            if actual_credentials:
                exec_kwargs[field_name] = actual_credentials
            else:
                return ErrorResponse(
                    message=f"Failed to retrieve credentials for {field_name}",
                    session_id=session_id,
                )

        # Coerce non-matching data types to the expected input schema.
        coerce_inputs_to_schema(input_data, block.input_schema)

        # Pre-execution credit check (courtesy; spend_credits is atomic)
        cost, cost_filter = block_usage_cost(block, input_data)
        has_cost = cost > 0
        _credit_db = credit_db()
        if has_cost:
            balance = await _credit_db.get_credits(user_id)
            if balance < cost:
                return ErrorResponse(
                    message=(
                        f"Insufficient credits to run '{block.name}'. "
                        "Please top up your credits to continue."
                    ),
                    session_id=session_id,
                )

        # Execute the block under the shared MCP wait cap. A block is
        # expected to finish in MAX_TOOL_WAIT_SECONDS; if it doesn't, the
        # MCP handler would block the stream close to the idle timeout.
        # wait_for cancels the generator on timeout, but the finally below
        # still settles billing via asyncio.shield — external side effects
        # may already have landed and the user should be charged for them.
        outputs: dict[str, list[Any]] = defaultdict(list)
        charge_handled = False
        try:
            await asyncio.wait_for(
                _collect_block_outputs(block, input_data, exec_kwargs, outputs),
                timeout=MAX_TOOL_WAIT_SECONDS,
            )

            # Normal (non-cancelled) path. Mark charge_handled BEFORE the
            # await so an outer cancellation landing mid-charge can't race
            # the finally block into a double-charge. asyncio.shield keeps
            # the spend running to completion even if the outer awaitable
            # is cancelled.
            if has_cost:
                charge_handled = True
                await asyncio.shield(
                    _charge_block_credits(
                        _credit_db,
                        user_id=user_id,
                        block_name=block.name,
                        block_id=block_id,
                        node_exec_id=node_exec_id,
                        cost=cost,
                        cost_filter=cost_filter,
                        synthetic_graph_id=synthetic_graph_id,
                        synthetic_node_id=synthetic_node_id,
                    )
                )

            return BlockOutputResponse(
                message=f"Block '{block.name}' executed successfully",
                block_id=block_id,
                block_name=block.name,
                outputs=dict(outputs),
                success=True,
                session_id=session_id,
            )
        except asyncio.TimeoutError:
            # Structured record of tool-call timeouts (SECRT-2247 part 3).
            # Grep prod logs for `copilot_tool_timeout` to find tools that
            # keep hitting the cap — candidates for prompt tuning or
            # escalation to the async start+poll pattern.
            logger.warning(
                "copilot_tool_timeout tool=run_block block=%s block_id=%s "
                "input_keys=%s user=%s session=%s cap_s=%d",
                block.name,
                block_id,
                sorted(input_data.keys()),
                user_id,
                session_id,
                MAX_TOOL_WAIT_SECONDS,
            )
            return ErrorResponse(
                message=(
                    f"Block '{block.name}' exceeded the "
                    f"{MAX_TOOL_WAIT_SECONDS}s single-tool wait cap and was "
                    "cancelled. Long-running work should go through run_agent "
                    "(graph executions) or run_sub_session (sub-AutoPilot "
                    "tasks) — those use async start+poll so nothing blocks "
                    "the chat stream."
                ),
                session_id=session_id,
            )
        finally:
            # Sentry r3105079148: asyncio.wait_for raises CancelledError into
            # the generator. Normal `except Exception` doesn't catch it, so
            # without this finally a cancelled block would skip credit
            # charging entirely while external side effects still landed.
            # Only run when the normal-path charge was NOT reached (the flag
            # is set before the await, so any cancellation during charge still
            # sets it and avoids double-billing — r3105216985).
            if has_cost and outputs and not charge_handled:
                await asyncio.shield(
                    _charge_block_credits(
                        _credit_db,
                        user_id=user_id,
                        block_name=block.name,
                        block_id=block_id,
                        node_exec_id=node_exec_id,
                        cost=cost,
                        cost_filter=cost_filter,
                        synthetic_graph_id=synthetic_graph_id,
                        synthetic_node_id=synthetic_node_id,
                    )
                )

    except BlockError as e:
        logger.warning("Block execution failed: %s", e)
        return ErrorResponse(
            message=f"Block execution failed: {e}",
            error=str(e),
            session_id=session_id,
        )
    except Exception as e:
        logger.error("Unexpected error executing block: %s", e, exc_info=True)
        return ErrorResponse(
            message=f"Failed to execute block: {str(e)}",
            error=str(e),
            session_id=session_id,
        )