def handle_event(
    handlers: list[BaseCallbackHandler],
    event_name: str,
    ignore_condition_name: str | None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Generic event handler for `CallbackManager`.

    Args:
        handlers: The list of handlers that will handle the event.
        event_name: The name of the event (e.g., `'on_llm_start'`).
        ignore_condition_name: Name of the attribute defined on handler that if `True`
            will cause the handler to be skipped for the given event.
        *args: The arguments to pass to the event handler.
        **kwargs: The keyword arguments to pass to the event handler

    """
    coros: list[Coroutine[Any, Any, Any]] = []

    try:
        message_strings: list[str] | None = None
        for handler in handlers:
            try:
                if ignore_condition_name is None or not getattr(
                    handler, ignore_condition_name
                ):
                    event = getattr(handler, event_name)(*args, **kwargs)
                    if asyncio.iscoroutine(event):
                        coros.append(event)
            except NotImplementedError as e:
                if event_name == "on_chat_model_start":
                    if message_strings is None:
                        message_strings = [get_buffer_string(m) for m in args[1]]
                    handle_event(
                        [handler],
                        "on_llm_start",
                        "ignore_llm",
                        args[0],
                        message_strings,
                        *args[2:],
                        **kwargs,
                    )
                else:
                    handler_name = handler.__class__.__name__
                    logger.warning(
                        "NotImplementedError in %s.%s callback: %s",
                        handler_name,
                        event_name,
                        repr(e),
                    )
            except Exception as e:
                logger.warning(
                    "Error in %s.%s callback: %s",
                    handler.__class__.__name__,
                    event_name,
                    repr(e),
                )
                if handler.raise_error:
                    raise
    finally:
        if coros:
            try:
                # Raises RuntimeError if there is no current event loop.
                asyncio.get_running_loop()
                loop_running = True
            except RuntimeError:
                loop_running = False

            if loop_running:
                # If we try to submit this coroutine to the running loop
                # we end up in a deadlock, as we'd have gotten here from a
                # running coroutine, which we cannot interrupt to run this one.
                # The solution is to run the synchronous function on the globally shared
                # thread pool executor to avoid blocking the main event loop.
                _executor().submit(
                    cast("Callable", copy_context().run), _run_coros, coros
                ).result()
            else:
                # If there's no running loop, we can run the coroutines directly.
                _run_coros(coros)