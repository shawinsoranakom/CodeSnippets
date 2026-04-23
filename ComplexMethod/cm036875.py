async def test_code_interpreter_streaming(
    client: OpenAI,
    model_name: str,
    pairs_of_event_types: dict[str, str],
):
    tools = [{"type": "code_interpreter", "container": {"type": "auto"}}]
    input_text = (
        "Calculate 123 * 456 using python. "
        "The python interpreter is not stateful and you must "
        "print to see the output."
    )

    def _has_code_interpreter(evts: list) -> bool:
        return events_contain_type(evts, "code_interpreter")

    events = await retry_streaming_for(
        client,
        model=model_name,
        validate_events=_has_code_interpreter,
        input=input_text,
        tools=tools,
        temperature=0.0,
        instructions=(
            "You must use the Python tool to execute code. Never simulate execution."
        ),
    )

    event_types = [e.type for e in events]
    event_types_set = set(event_types)
    logger.info(
        "\n====== Code Interpreter Streaming Diagnostics ======\n"
        "Event count: %d\n"
        "Event types (in order): %s\n"
        "Unique event types: %s\n"
        "====================================================",
        len(events),
        event_types,
        sorted(event_types_set),
    )

    # Structural validation (pairing, ordering, field consistency)
    validate_streaming_event_stack(events, pairs_of_event_types)

    # Validate code interpreter item fields
    for event in events:
        if (
            event.type == "response.output_item.added"
            and hasattr(event.item, "type")
            and event.item.type == "code_interpreter_call"
        ):
            assert event.item.status == "in_progress"
        elif event.type == "response.code_interpreter_call_code.done":
            assert event.code is not None
        elif (
            event.type == "response.output_item.done"
            and hasattr(event.item, "type")
            and event.item.type == "code_interpreter_call"
        ):
            assert event.item.status == "completed"
            assert event.item.code is not None