async def handle_info(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle an info request via a subscription."""
    data = {}
    pending_info: dict[tuple[str, str], asyncio.Task] = {}

    async for domain, domain_data in _registered_domain_data(hass):
        for key, value in domain_data["info"].items():
            if asyncio.iscoroutine(value):
                value = asyncio.create_task(value)
            if isinstance(value, asyncio.Task):
                pending_info[(domain, key)] = value
                domain_data["info"][key] = {"type": "pending"}
            else:
                domain_data["info"][key] = _format_value(value)

        data[domain] = domain_data

    # Confirm subscription
    connection.send_result(msg["id"])

    stop_event = asyncio.Event()
    connection.subscriptions[msg["id"]] = stop_event.set

    # Send initial data
    connection.send_message(
        websocket_api.messages.event_message(
            msg["id"], {"type": "initial", "data": data}
        )
    )

    # If nothing pending, wrap it up.
    if not pending_info:
        connection.send_message(
            websocket_api.messages.event_message(msg["id"], {"type": "finish"})
        )
        return

    tasks: set[asyncio.Task] = {
        asyncio.create_task(stop_event.wait()),
        *pending_info.values(),
    }
    pending_lookup = {val: key for key, val in pending_info.items()}

    # One task is the stop_event.wait() and is always there
    while len(tasks) > 1 and not stop_event.is_set():
        # Wait for first completed task
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        if stop_event.is_set():
            for task in tasks:
                task.cancel()
            return

        # Update subscription of all finished tasks
        for result in done:
            domain, key = pending_lookup[result]
            event_msg: dict[str, Any] = {
                "type": "update",
                "domain": domain,
                "key": key,
            }

            if exception := result.exception():
                _LOGGER.error(
                    "Error fetching system info for %s - %s",
                    domain,
                    key,
                    exc_info=(type(exception), exception, exception.__traceback__),
                )
                event_msg["success"] = False
                event_msg["error"] = {"type": "failed", "error": "unknown"}
            else:
                event_msg["success"] = True
                event_msg["data"] = _format_value(result.result())

            connection.send_message(
                websocket_api.messages.event_message(msg["id"], event_msg)
            )

    connection.send_message(
        websocket_api.messages.event_message(msg["id"], {"type": "finish"})
    )