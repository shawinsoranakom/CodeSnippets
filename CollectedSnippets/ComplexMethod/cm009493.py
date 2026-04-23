async def _ahandle_event_for_handler(
    handler: BaseCallbackHandler,
    event_name: str,
    ignore_condition_name: str | None,
    *args: Any,
    **kwargs: Any,
) -> None:
    try:
        if ignore_condition_name is None or not getattr(handler, ignore_condition_name):
            event = getattr(handler, event_name)
            if asyncio.iscoroutinefunction(event):
                await event(*args, **kwargs)
            elif handler.run_inline:
                event(*args, **kwargs)
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    cast(
                        "Callable",
                        functools.partial(copy_context().run, event, *args, **kwargs),
                    ),
                )
    except NotImplementedError as e:
        if event_name == "on_chat_model_start":
            message_strings = [get_buffer_string(m) for m in args[1]]
            await _ahandle_event_for_handler(
                handler,
                "on_llm_start",
                "ignore_llm",
                args[0],
                message_strings,
                *args[2:],
                **kwargs,
            )
        else:
            logger.warning(
                "NotImplementedError in %s.%s callback: %s",
                handler.__class__.__name__,
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