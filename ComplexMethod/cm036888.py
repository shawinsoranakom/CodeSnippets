def _validate_event_pairing(events: list, pairs_of_event_types: dict[str, str]) -> None:
    """Validate that streaming events are properly nested/paired.

    Derives push/pop sets from *pairs_of_event_types* so that every
    start/end pair in the dict is handled automatically.
    """
    start_events = set(pairs_of_event_types.values())
    end_events = set(pairs_of_event_types.keys())

    stack: list[str] = []
    for event in events:
        etype = event.type
        if etype in end_events:
            expected_start = pairs_of_event_types[etype]
            assert stack and stack[-1] == expected_start, (
                f"Stack mismatch for {etype}: "
                f"expected {expected_start}, "
                f"got {stack[-1] if stack else '<empty>'}"
            )
            stack.pop()
        elif etype in start_events:
            # Consecutive deltas of the same type share a single stack slot.
            if etype.endswith("delta") and stack and stack[-1] == etype:
                continue
            stack.append(etype)
        # else: passthrough event (e.g. response.in_progress,
        # web_search_call.searching, code_interpreter_call.interpreting)
    assert len(stack) == 0, f"Unclosed events on stack: {stack}"