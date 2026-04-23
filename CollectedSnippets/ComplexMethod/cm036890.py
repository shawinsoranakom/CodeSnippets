def _validate_field_consistency(events: list) -> None:
    """Validate item_id, output_index, and content_index consistency.

    Tracks the active output item established by ``output_item.added``
    and verifies that all subsequent events for that item carry matching
    identifiers until ``output_item.done`` closes it.
    """
    _SESSION_EVENTS = {
        "response.created",
        "response.in_progress",
        "response.completed",
    }

    active_item_id: str | None = None
    active_output_index: int | None = None
    last_output_index: int = -1
    active_content_index: int | None = None

    for event in events:
        etype = event.type

        if etype in _SESSION_EVENTS:
            continue

        # --- output_item.added: opens a new item ------------------
        if etype == "response.output_item.added":
            item = getattr(event, "item", None)
            output_index = getattr(event, "output_index", None)

            assert item is not None, "output_item.added must have an item"
            item_id = getattr(item, "id", None)
            assert item_id, "output_item.added item must have an id"

            # output_index must be non-decreasing across items
            if output_index is not None:
                assert output_index >= last_output_index, (
                    f"output_index went backwards: {output_index} < {last_output_index}"
                )
                last_output_index = output_index

            active_item_id = item_id
            active_output_index = output_index
            active_content_index = None
            continue

        # --- output_item.done: closes the active item -------------
        if etype == "response.output_item.done":
            item = getattr(event, "item", None)
            output_index = getattr(event, "output_index", None)

            assert item is not None, "output_item.done must have an item"
            done_item_id = getattr(item, "id", None)

            if active_item_id is not None and done_item_id:
                assert done_item_id == active_item_id, (
                    f"output_item.done item.id mismatch: "
                    f"expected {active_item_id}, got {done_item_id}"
                )
            if active_output_index is not None and output_index is not None:
                assert output_index == active_output_index, (
                    f"output_item.done output_index mismatch: "
                    f"expected {active_output_index}, got {output_index}"
                )

            active_item_id = None
            active_output_index = None
            active_content_index = None
            continue

        # --- content_part / reasoning_part added: sets content_index
        if etype in (
            "response.content_part.added",
            "response.reasoning_part.added",
        ):
            _assert_item_fields(event, etype, active_item_id, active_output_index)
            active_content_index = getattr(event, "content_index", None)
            continue

        # --- all other item-level events --------------------------
        _assert_item_fields(event, etype, active_item_id, active_output_index)

        # content_index (only meaningful on events that carry it)
        content_index = getattr(event, "content_index", None)
        if content_index is not None and active_content_index is not None:
            assert content_index == active_content_index, (
                f"{etype} content_index mismatch: "
                f"expected {active_content_index}, got {content_index}"
            )