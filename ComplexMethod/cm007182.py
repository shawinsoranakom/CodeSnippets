async def log_transaction(
    flow_id: str | UUID,
    source: Vertex,
    status: str,
    target: Vertex | None = None,
    error: str | Exception | None = None,
    outputs: dict[str, Any] | None = None,
) -> None:
    """Asynchronously logs a transaction record for a vertex in a flow if transaction storage is enabled.

    Uses the pluggable TransactionService to log transactions. When running within langflow,
    the concrete TransactionService implementation persists to the database.
    When running standalone (lfx only), transactions are not persisted.

    Args:
        flow_id: The flow ID
        source: The source vertex (component being executed)
        status: Transaction status (success/error)
        target: Optional target vertex (for data transfer logging)
        error: Optional error information
        outputs: Optional explicit outputs dict (component execution results)
    """
    try:
        # Guard against null source
        if source is None:
            return

        # Get the transaction service via dependency injection
        from lfx.services.deps import get_transaction_service

        transaction_service = get_transaction_service()

        # If no transaction service is available or it's disabled, skip logging
        if transaction_service is None or not transaction_service.is_enabled():
            return

        # Resolve flow_id
        if not flow_id:
            if source.graph.flow_id:
                flow_id = source.graph.flow_id
            else:
                return

        # Convert UUID to string for the service interface
        flow_id_str = str(flow_id) if isinstance(flow_id, UUID) else flow_id

        # Prepare inputs and outputs
        inputs = _vertex_to_primitive_dict(source) if source else None
        target_outputs = _vertex_to_primitive_dict(target) if target else None
        transaction_outputs = outputs if outputs is not None else target_outputs

        # Log transaction via the service
        await transaction_service.log_transaction(
            flow_id=flow_id_str,
            vertex_id=source.id,
            inputs=inputs,
            outputs=transaction_outputs,
            status=status,
            target_id=target.id if target else None,
            error=str(error) if error else None,
        )

    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Error logging transaction: {exc!s}")