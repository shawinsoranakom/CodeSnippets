async def log_system_credential_cost(
    node_exec: NodeExecutionEntry,
    block: Block,
    stats: NodeExecutionStats,
    db_client: "DatabaseManagerAsyncClient",
) -> None:
    """Check if a system credential was used and log the platform cost.

    Routes through DatabaseManagerAsyncClient so the write goes via the
    message-passing DB service rather than calling Prisma directly (which
    is not connected in the executor process).

    Logs only the first matching system credential field (one log per
    execution). Any unexpected error is caught and logged — cost logging
    is strictly best-effort and must never disrupt block execution.

    Note: costMicrodollars is left null for providers that don't return
    a USD cost. The credit_cost in metadata captures our internal credit
    charge as a proxy.
    """
    try:
        if node_exec.execution_context.dry_run:
            return

        input_data = node_exec.inputs
        input_model = cast(type[BlockSchema], block.input_schema)

        for field_name in input_model.get_credentials_fields():
            cred_data = input_data.get(field_name)
            if not cred_data or not isinstance(cred_data, dict):
                continue
            cred_id = cred_data.get("id", "")
            if not cred_id or not is_system_credential(cred_id):
                continue

            model_name = _extract_model_name(input_data.get("model"))

            credit_cost, _ = block_usage_cost(block=block, input_data=input_data)

            provider_name = cred_data.get("provider", "unknown")
            tracking_type, tracking_amount = resolve_tracking(
                provider=provider_name,
                stats=stats,
                input_data=input_data,
            )

            # Only treat provider_cost as USD when the tracking type says so.
            # For other types (items, characters, per_run, ...) the
            # provider_cost field holds the raw amount, not a dollar value.
            # Use tracking_amount (the normalized value from resolve_tracking)
            # rather than raw stats.provider_cost to avoid unit mismatches.
            cost_microdollars = None
            if tracking_type == "cost_usd":
                cost_microdollars = usd_to_microdollars(tracking_amount)

            meta: dict[str, Any] = {
                "tracking_type": tracking_type,
                "tracking_amount": tracking_amount,
            }
            if credit_cost is not None:
                meta["credit_cost"] = credit_cost
            if stats.provider_cost is not None:
                # Use 'provider_cost_raw' — the value's unit varies by tracking
                # type (USD for cost_usd, count for items/characters/per_run, etc.)
                meta["provider_cost_raw"] = stats.provider_cost

            _schedule_log(
                db_client,
                PlatformCostEntry(
                    user_id=node_exec.user_id,
                    graph_exec_id=node_exec.graph_exec_id,
                    node_exec_id=node_exec.node_exec_id,
                    graph_id=node_exec.graph_id,
                    node_id=node_exec.node_id,
                    block_id=node_exec.block_id,
                    block_name=block.name,
                    provider=provider_name,
                    credential_id=cred_id,
                    cost_microdollars=cost_microdollars,
                    input_tokens=stats.input_token_count,
                    output_tokens=stats.output_token_count,
                    cache_read_tokens=stats.cache_read_token_count or None,
                    cache_creation_tokens=stats.cache_creation_token_count or None,
                    data_size=stats.output_size if stats.output_size > 0 else None,
                    duration=stats.walltime if stats.walltime > 0 else None,
                    model=model_name,
                    tracking_type=tracking_type,
                    tracking_amount=tracking_amount,
                    metadata=meta,
                ),
            )
            return  # One log per execution is enough
    except Exception:
        logger.exception("log_system_credential_cost failed unexpectedly")