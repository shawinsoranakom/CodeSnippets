async def handle_devices_execute(
    hass: HomeAssistant, data: RequestData, payload: dict[str, Any]
) -> dict[str, Any]:
    """Handle action.devices.EXECUTE request.

    https://developers.google.com/assistant/smarthome/develop/process-intents#EXECUTE
    """
    entities: dict[str, GoogleEntity] = {}
    executions: dict[str, list[Any]] = {}
    results: dict[str, dict[str, Any]] = {}

    for command in payload["commands"]:
        hass.bus.async_fire(
            EVENT_COMMAND_RECEIVED,
            {
                "request_id": data.request_id,
                ATTR_ENTITY_ID: [device["id"] for device in command["devices"]],
                "execution": command["execution"],
                "source": data.source,
            },
            context=data.context,
        )

        for device, execution in product(command["devices"], command["execution"]):
            entity_id = device["id"]

            # Happens if error occurred. Skip entity for further processing
            if entity_id in results:
                continue

            if entity_id in entities:
                executions[entity_id].append(execution)
                continue

            if (state := hass.states.get(entity_id)) is None:
                results[entity_id] = {
                    "ids": [entity_id],
                    "status": "ERROR",
                    "errorCode": ERR_DEVICE_OFFLINE,
                }
                continue

            entities[entity_id] = GoogleEntity(hass, data.config, state)
            executions[entity_id] = [execution]

    try:
        execute_results = await asyncio.wait_for(
            asyncio.shield(
                asyncio.gather(
                    *(
                        _entity_execute(entities[entity_id], data, execution)
                        for entity_id, execution in executions.items()
                    )
                )
            ),
            EXECUTE_LIMIT,
        )
        results.update(
            {
                entity_id: result
                for entity_id, result in zip(executions, execute_results, strict=False)
                if result is not None
            }
        )
    except TimeoutError:
        pass

    final_results = list(results.values())

    for entity in entities.values():
        if entity.entity_id in results:
            continue

        entity.async_update()

        final_results.append(
            {
                "ids": [entity.entity_id],
                "status": "SUCCESS",
                "states": entity.query_serialize(),
            }
        )

    return {"commands": final_results}