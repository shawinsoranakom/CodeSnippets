async def _astream_events_implementation_v2(
    runnable: Runnable[Input, Output],
    value: Any,
    config: RunnableConfig | None = None,
    *,
    include_names: Sequence[str] | None = None,
    include_types: Sequence[str] | None = None,
    include_tags: Sequence[str] | None = None,
    exclude_names: Sequence[str] | None = None,
    exclude_types: Sequence[str] | None = None,
    exclude_tags: Sequence[str] | None = None,
    **kwargs: Any,
) -> AsyncIterator[StandardStreamEvent]:
    """Implementation of the astream events API for v2 runnables."""
    event_streamer = _AstreamEventsCallbackHandler(
        include_names=include_names,
        include_types=include_types,
        include_tags=include_tags,
        exclude_names=exclude_names,
        exclude_types=exclude_types,
        exclude_tags=exclude_tags,
    )

    # Assign the stream handler to the config
    config = ensure_config(config)
    if "run_id" in config:
        run_id = cast("UUID", config["run_id"])
    else:
        run_id = uuid7()
        config["run_id"] = run_id
    callbacks = config.get("callbacks")
    if callbacks is None:
        config["callbacks"] = [event_streamer]
    elif isinstance(callbacks, list):
        config["callbacks"] = [*callbacks, event_streamer]
    elif isinstance(callbacks, BaseCallbackManager):
        callbacks = callbacks.copy()
        callbacks.add_handler(event_streamer, inherit=True)
        config["callbacks"] = callbacks
    else:
        msg = (
            f"Unexpected type for callbacks: {callbacks}."
            "Expected None, list or AsyncCallbackManager."
        )
        raise ValueError(msg)

    # Call the runnable in streaming mode,
    # add each chunk to the output stream
    async def consume_astream() -> None:
        try:
            # if astream also calls tap_output_aiter this will be a no-op
            async with aclosing(runnable.astream(value, config, **kwargs)) as stream:
                async for _ in event_streamer.tap_output_aiter(run_id, stream):
                    # All the content will be picked up
                    pass
        finally:
            await event_streamer.send_stream.aclose()

    # Start the runnable in a task, so we can start consuming output
    task = asyncio.create_task(consume_astream())

    first_event_sent = False
    first_event_run_id = None

    try:
        async for event in event_streamer:
            if not first_event_sent:
                first_event_sent = True
                # This is a work-around an issue where the inputs into the
                # chain are not available until the entire input is consumed.
                # As a temporary solution, we'll modify the input to be the input
                # that was passed into the chain.
                event["data"]["input"] = value
                first_event_run_id = event["run_id"]
                yield event
                continue

            # If it's the end event corresponding to the root runnable
            # we don't include the input in the event since it's guaranteed
            # to be included in the first event.
            if (
                event["run_id"] == first_event_run_id
                and event["event"].endswith("_end")
                and "input" in event["data"]
            ):
                del event["data"]["input"]

            yield event
    except asyncio.CancelledError as exc:
        # Cancel the task if it's still running
        task.cancel(exc.args[0] if exc.args else None)
        raise
    finally:
        # Cancel the task if it's still running
        task.cancel()
        # Await it anyway, to run any cleanup code, and propagate any exceptions
        with contextlib.suppress(asyncio.CancelledError):
            await task