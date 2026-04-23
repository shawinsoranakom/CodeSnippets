async def _async_handle_entity_calls(
    entity_calls: list[tuple[Entity, Coroutine[Any, Any, ServiceResponse]]],
    *,
    context: Context,
) -> EntityServiceResponse:
    """Handle calls for entities."""

    async def _with_context(
        entity: Entity, coro: Coroutine[Any, Any, ServiceResponse]
    ) -> ServiceResponse:
        entity.async_set_context(context)
        return await coro

    if len(entity_calls) == 1:
        # Single entity case avoids creating task
        entity, coro = entity_calls[0]
        single_result = await entity.async_request_call(_with_context(entity, coro))
        if entity.should_poll:
            # Context can expire, so set it again before we update
            entity.async_set_context(context)
            await entity.async_update_ha_state(True)
        return {entity.entity_id: single_result}

    entities = [entity for entity, _ in entity_calls]
    results: list[ServiceResponse | BaseException] = await asyncio.gather(
        *[
            entity.async_request_call(_with_context(entity, coro))
            for entity, coro in entity_calls
        ],
        return_exceptions=True,
    )

    response_data: EntityServiceResponse = {}
    for entity, result in zip(entities, results, strict=True):
        if isinstance(result, BaseException):
            raise result from None
        response_data[entity.entity_id] = result

    tasks: list[asyncio.Task[None]] = []
    for entity in entities:
        if not entity.should_poll:
            continue
        # Context can expire, so set it again before we update
        entity.async_set_context(context)
        tasks.append(create_eager_task(entity.async_update_ha_state(True)))

    if tasks:
        done, pending = await asyncio.wait(tasks)
        assert not pending
        for future in done:
            future.result()

    return response_data