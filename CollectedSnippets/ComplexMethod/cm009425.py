async def _astream_events_implementation_v1(
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
    stream = LogStreamCallbackHandler(
        auto_close=False,
        include_names=include_names,
        include_types=include_types,
        include_tags=include_tags,
        exclude_names=exclude_names,
        exclude_types=exclude_types,
        exclude_tags=exclude_tags,
        _schema_format="streaming_events",
    )

    run_log = RunLog(state=None)  # type: ignore[arg-type]
    encountered_start_event = False

    root_event_filter = _RootEventFilter(
        include_names=include_names,
        include_types=include_types,
        include_tags=include_tags,
        exclude_names=exclude_names,
        exclude_types=exclude_types,
        exclude_tags=exclude_tags,
    )

    config = ensure_config(config)
    root_tags = config.get("tags", [])
    root_metadata = config.get("metadata", {})
    root_name = config.get("run_name", runnable.get_name())

    async for log in _astream_log_implementation(
        runnable,
        value,
        config=config,
        stream=stream,
        diff=True,
        with_streamed_output_list=True,
        **kwargs,
    ):
        run_log += log

        if not encountered_start_event:
            # Yield the start event for the root runnable.
            encountered_start_event = True
            state = run_log.state.copy()

            event = StandardStreamEvent(
                event=f"on_{state['type']}_start",
                run_id=state["id"],
                name=root_name,
                tags=root_tags,
                metadata=root_metadata,
                data={
                    "input": value,
                },
                parent_ids=[],  # Not supported in v1
            )

            if root_event_filter.include_event(event, state["type"]):
                yield event

        paths = {
            op["path"].split("/")[2]
            for op in log.ops
            if op["path"].startswith("/logs/")
        }
        # Elements in a set should be iterated in the same order
        # as they were inserted in modern python versions.
        for path in paths:
            data: EventData = {}
            log_entry: LogEntry = run_log.state["logs"][path]
            if log_entry["end_time"] is None:
                event_type = "stream" if log_entry["streamed_output"] else "start"
            else:
                event_type = "end"

            if event_type == "start":
                # Include the inputs with the start event if they are available.
                # Usually they will NOT be available for components that operate
                # on streams, since those components stream the input and
                # don't know its final value until the end of the stream.
                inputs = log_entry.get("inputs")
                if inputs is not None:
                    data["input"] = inputs

            if event_type == "end":
                inputs = log_entry.get("inputs")
                if inputs is not None:
                    data["input"] = inputs

                # None is a VALID output for an end event
                data["output"] = log_entry["final_output"]

            if event_type == "stream":
                num_chunks = len(log_entry["streamed_output"])
                if num_chunks != 1:
                    msg = (
                        f"Expected exactly one chunk of streamed output, "
                        f"got {num_chunks} instead. This is impossible. "
                        f"Encountered in: {log_entry['name']}"
                    )
                    raise AssertionError(msg)

                data = {"chunk": log_entry["streamed_output"][0]}
                # Clean up the stream, we don't need it anymore.
                # And this avoids duplicates as well!
                log_entry["streamed_output"] = []

            yield StandardStreamEvent(
                event=f"on_{log_entry['type']}_{event_type}",
                name=log_entry["name"],
                run_id=log_entry["id"],
                tags=log_entry["tags"],
                metadata=log_entry["metadata"],
                data=data,
                parent_ids=[],  # Not supported in v1
            )

        # Finally, we take care of the streaming output from the root chain
        # if there is any.
        state = run_log.state
        if state["streamed_output"]:
            num_chunks = len(state["streamed_output"])
            if num_chunks != 1:
                msg = (
                    f"Expected exactly one chunk of streamed output, "
                    f"got {num_chunks} instead. This is impossible. "
                    f"Encountered in: {state['name']}"
                )
                raise AssertionError(msg)

            data = {"chunk": state["streamed_output"][0]}
            # Clean up the stream, we don't need it anymore.
            state["streamed_output"] = []

            event = StandardStreamEvent(
                event=f"on_{state['type']}_stream",
                run_id=state["id"],
                tags=root_tags,
                metadata=root_metadata,
                name=root_name,
                data=data,
                parent_ids=[],  # Not supported in v1
            )
            if root_event_filter.include_event(event, state["type"]):
                yield event

    state = run_log.state

    # Finally yield the end event for the root runnable.
    event = StandardStreamEvent(
        event=f"on_{state['type']}_end",
        name=root_name,
        run_id=state["id"],
        tags=root_tags,
        metadata=root_metadata,
        data={
            "output": state["final_output"],
        },
        parent_ids=[],  # Not supported in v1
    )
    if root_event_filter.include_event(event, state["type"]):
        yield event