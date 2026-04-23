async def resolve_connections_for_operations(
    *,
    clients: WxOClient,
    user_id: IdLike,
    db: AsyncSession,
    existing_app_ids: list[str],
    raw_connections_to_create: list[RawConnectionCreatePlan],
    error_prefix: str,
    validate_connection_fn: Callable[..., Awaitable[object]] = validate_connection,
    create_connection_fn: Callable[..., Awaitable[str]] = create_connection_with_conflict_mapping,
) -> ConnectionResolutionResult:
    logger.debug(
        "resolve_connections_for_operations: existing_app_ids=%s, raw_to_create=%d",
        existing_app_ids,
        len(raw_connections_to_create),
    )
    operation_to_provider_app_id = {app_id: app_id for app_id in existing_app_ids}
    resolved_connections: dict[str, str] = {}

    if existing_app_ids:
        existing_connections: list[object] = await asyncio.gather(
            *(retry_create(validate_connection_fn, clients.connections, app_id=app_id) for app_id in existing_app_ids)
        )
        for app_id, connection in zip(existing_app_ids, existing_connections, strict=True):
            resolved_connections[app_id] = connection.connection_id  # type: ignore[attr-defined]

    if not raw_connections_to_create:
        return ConnectionResolutionResult(
            operation_to_provider_app_id=operation_to_provider_app_id,
            resolved_connections=resolved_connections,
            created_app_ids=[],
        )

    created_connections_results = await asyncio.gather(
        *(
            create_connection_fn(
                clients=clients,
                app_id=create_plan.provider_app_id,
                payload=create_plan.payload,
                user_id=user_id,
                db=db,
                error_prefix=error_prefix,
            )
            for create_plan in raw_connections_to_create
        ),
        return_exceptions=True,
    )

    create_connection_errors: list[Exception] = []
    created_app_ids_journal: list[str] = []
    for result in created_connections_results:
        if isinstance(result, BaseException):
            if isinstance(result, Exception):
                create_connection_errors.append(result)
            else:
                create_connection_errors.append(
                    RuntimeError(f"Connection create failed with non-standard exception: {type(result).__name__}")
                )
            continue
        created_app_ids_journal.append(result)
    created_app_ids = list(dict.fromkeys(created_app_ids_journal))
    if create_connection_errors:
        logger.debug(
            "resolve_connections_for_operations: %d errors, created_app_ids=%s",
            len(create_connection_errors),
            created_app_ids,
        )
        raise ConnectionCreateBatchError(created_app_ids=created_app_ids, errors=create_connection_errors)

    validated_created_connections: list[object] = await asyncio.gather(
        *(
            retry_create(
                validate_connection_fn,
                clients.connections,
                app_id=create_plan.provider_app_id,
            )
            for create_plan in raw_connections_to_create
        )
    )
    for create_plan, connection in zip(raw_connections_to_create, validated_created_connections, strict=True):
        operation_to_provider_app_id[create_plan.operation_app_id] = create_plan.provider_app_id
        resolved_connections[create_plan.provider_app_id] = connection.connection_id  # type: ignore[attr-defined]

    logger.debug(
        "resolve_connections_for_operations: resolved_connections=%s, created_app_ids=%s",
        resolved_connections,
        created_app_ids,
    )

    return ConnectionResolutionResult(
        operation_to_provider_app_id=operation_to_provider_app_id,
        resolved_connections=resolved_connections,
        created_app_ids=created_app_ids,
    )