async def trigger_subscription_callback(
    hass: HomeAssistant,
    client: MagicMock,
    event: EventType = EventType.PLAYER_UPDATED,
    object_id: str | None = None,
    data: Any = None,
) -> None:
    """Trigger a subscription callback."""
    # trigger callback on all subscribers
    for sub in client.subscribe.call_args_list:
        cb_func = sub.kwargs.get("cb_func", sub.args[0])
        event_filter = sub.kwargs.get(
            "event_filter", sub.args[1] if len(sub.args) > 1 else None
        )
        id_filter = sub.kwargs.get(
            "id_filter", sub.args[2] if len(sub.args) > 2 else None
        )
        if not (
            event_filter is None
            or event == event_filter
            or (isinstance(event_filter, list) and event in event_filter)
        ):
            continue
        if not (
            id_filter is None
            or object_id == id_filter
            or (isinstance(id_filter, list) and object_id in id_filter)
        ):
            continue

        mass_event = MassEvent(
            event=event,
            object_id=object_id,
            data=data,
        )
        if inspect.iscoroutinefunction(cb_func):
            await cb_func(mass_event)
        else:
            cb_func(mass_event)

    await hass.async_block_till_done()